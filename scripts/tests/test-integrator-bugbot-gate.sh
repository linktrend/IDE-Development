#!/usr/bin/env bash
set -euo pipefail
bugbot_state() {
  echo "$1" | jq -r '
    [.[] | select(.name=="Cursor Bugbot")] as $b
    | if ($b|length)==0 then "missing"
      elif any($b[]; .state=="PENDING" or .state=="QUEUED" or .state=="IN_PROGRESS") then "pending"
      elif all($b[]; .state=="SUCCESS") then "success"
      else "not_success"
      end'
}
[ "$(bugbot_state '[{"name":"Cursor Bugbot","state":"SUCCESS"}]')" = "success" ]
[ "$(bugbot_state '[{"name":"Cursor Bugbot","state":"NEUTRAL"}]')" = "not_success" ]
[ "$(bugbot_state '[{"name":"Cursor Bugbot","state":"PENDING"}]')" = "pending" ]
[ "$(bugbot_state '[{"name":"Verify IDE Development","state":"SUCCESS"}]')" = "missing" ]
[ "$(bugbot_state '[{"name":"Cursor Bugbot","state":"SUCCESS"},{"name":"Cursor Bugbot","state":"NEUTRAL"}]')" = "not_success" ]
[ "$(bugbot_state '[{"name":"Cursor Bugbot","state":"SUCCESS"},{"name":"Cursor Bugbot","state":"SUCCESS"}]')" = "success" ]
echo "PASS: integrator Bugbot gate cases"
