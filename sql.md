SET SERVEROUTPUT ON
SET LINESIZE 200
SET PAGESIZE 1000

DECLARE
  v_seconds NUMBER := 5;  -- refresh interval in seconds
BEGIN
  FOR i IN 1..1000 LOOP  -- adjust number of iterations as needed
    dbms_output.put_line('--- Active Queries at ' || TO_CHAR(SYSDATE,'HH24:MI:SS') || ' ---');

    FOR r IN (
      SELECT s.sid,
             s.serial#,
             s.username,
             s.machine,
             s.program,
             q.sql_id,
             SUBSTR(q.sql_text,1,1000) AS sql_text,
             s.status,
             s.last_call_et AS seconds_running
      FROM   v$session s
      JOIN   v$sql q ON s.sql_id = q.sql_id
      WHERE  s.username IS NOT NULL
        AND  s.status = 'ACTIVE'
      ORDER BY s.last_call_et DESC
    )
    LOOP
      dbms_output.put_line(
        'SID=' || r.sid || ' | USER=' || r.username ||
        ' | SQL_ID=' || r.sql_id || 
        ' | Running=' || r.seconds_running || 's' ||
        CHR(10) || 'SQL: ' || r.sql_text || CHR(10)
      );
    END LOOP;

    dbms_lock.sleep(v_seconds); -- pause before next refresh
  END LOOP;
END;
/
