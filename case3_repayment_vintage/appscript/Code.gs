/**
 * Amar Bank Workshop Part 2 — Case 3
 * Google Apps Script: konsumsi data Snowflake dari Google Sheet via Snowflake SQL API.
 * Ini PENGGANTI alur lama (Looker Look -> Apps Script -> Sheet).
 *
 * Alur baru:  Snowflake (VW_PAYBACK_CURVE / VW_REPAYMENT_LONG)
 *             --> Snowflake SQL API (REST) --> Google Sheet --> formula diolah di sheet
 *
 * ---------------------------------------------------------------------------
 * SETUP (sekali):
 * 1. Buat Programmatic Access Token (PAT) di Snowsight:
 *      Admin -> Users & Roles -> pilih user -> Generate Token (atau:
 *      CREATE ... ; lihat docs "Programmatic access tokens").
 * 2. Di Apps Script: Project Settings -> Script Properties, tambahkan:
 *      SNOWFLAKE_ACCOUNT_URL  = https://<orgname>-<account>.snowflakecomputing.com
 *      SNOWFLAKE_PAT          = <token PAT Anda>
 *      SNOWFLAKE_WAREHOUSE    = GEN2_SMALL
 *      SNOWFLAKE_ROLE         = ACCOUNTADMIN
 *    (JANGAN hardcode token di kode — pakai Script Properties.)
 * 3. Simpan, refresh Sheet -> muncul menu "Snowflake".
 * ---------------------------------------------------------------------------
 */

var DB = 'AMAR_WORKSHOP_P2';
var SCHEMA = 'REPAYMENT';

function _cfg(key) {
  return PropertiesService.getScriptProperties().getProperty(key);
}

/** Panggil Snowflake SQL API, kembalikan {columns:[], rows:[[]]}. */
function snowflakeQuery(sql) {
  var url = _cfg('SNOWFLAKE_ACCOUNT_URL') + '/api/v2/statements';
  var payload = {
    statement: sql,
    timeout: 60,
    warehouse: _cfg('SNOWFLAKE_WAREHOUSE'),
    role: _cfg('SNOWFLAKE_ROLE'),
    database: DB,
    schema: SCHEMA
  };
  var options = {
    method: 'post',
    contentType: 'application/json',
    headers: {
      'Authorization': 'Bearer ' + _cfg('SNOWFLAKE_PAT'),
      'X-Snowflake-Authorization-Token-Type': 'PROGRAMMATIC_ACCESS_TOKEN',
      'Accept': 'application/json'
    },
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  };
  var resp = UrlFetchApp.fetch(url, options);
  var data = JSON.parse(resp.getContentText());
  if (resp.getResponseCode() >= 400) {
    throw new Error('Snowflake API error: ' + resp.getContentText());
  }
  var cols = (data.resultSetMetaData && data.resultSetMetaData.rowType || []).map(function (c) { return c.name; });
  var rows = data.data || [];
  return { columns: cols, rows: rows };
}

/** Tulis hasil query ke sheet bernama sheetName (dibersihkan dulu). */
function writeToSheet(sheetName, result) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sh = ss.getSheetByName(sheetName) || ss.insertSheet(sheetName);
  sh.clearContents();
  sh.getRange(1, 1, 1, result.columns.length).setValues([result.columns]);
  if (result.rows.length) {
    sh.getRange(2, 1, result.rows.length, result.columns.length).setValues(result.rows);
  }
  sh.getRange(1, 1, 1, result.columns.length).setFontWeight('bold');
}

/** === "Look" 1: Payback Curve (agregat, siap pakai) === */
function refreshPaybackCurve() {
  var sql =
    "SELECT MONTH_INDEX, APP_TYPE, " +
    "ROUND(AVG(PAYBACK_RATE)*100,2) AS PAYBACK_PCT, SUM(N_LOANS) AS N_LOANS " +
    "FROM " + DB + "." + SCHEMA + ".VW_PAYBACK_CURVE " +
    "GROUP BY 1,2 ORDER BY 1,2";
  writeToSheet('PaybackCurve', snowflakeQuery(sql));
  SpreadsheetApp.getActiveSpreadsheet().toast('PaybackCurve di-refresh dari Snowflake.');
}

/** === "Look" 2: raw vintage (untuk diolah ulang dgn formula di sheet) === */
function refreshVintageRaw() {
  var sql =
    "SELECT REF_NUM, APP_TYPE, LOAN_AMOUNT, MONTH_INDEX, PAYMENT, CUMULATIVE " +
    "FROM " + DB + "." + SCHEMA + ".VW_REPAYMENT_LONG " +
    "WHERE MONTH_INDEX <= 12 LIMIT 5000";
  writeToSheet('VintageRaw', snowflakeQuery(sql));
}

/**
 * Custom formula: =SNOWQUERY("SELECT ...")
 * Bisa dipakai langsung di cell; hasil tumpah (spill) sebagai array.
 * Ini menggantikan formula lama yang menarik dari Looker API.
 */
function SNOWQUERY(sql) {
  var r = snowflakeQuery(sql);
  return [r.columns].concat(r.rows);
}

/** Menu di Google Sheet */
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('Snowflake')
    .addItem('Refresh Payback Curve', 'refreshPaybackCurve')
    .addItem('Refresh Vintage Raw', 'refreshVintageRaw')
    .addToUi();
}
