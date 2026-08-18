#!/usr/bin/env bash
set -euo pipefail
bugbot_state() {
  echo "$1" | jq -r '
    [.[] | select(.name=="Linktrend Review Gate")] as $b
    | if ($b|length)==0 then "missing"
      else
        ($b | sort_by(.completedAt // .startedAt // "") | last | .state) as $s
        | if ($s=="PENDING" or $s=="QUEUED" or $s=="IN_PROGRESS") then "pending"
          elif ($s=="SUCCESS") then "success"
          else "not_success"
          end
      end'
}
[ "$(bugbot_state '[{"name":"Linktrend Review Gate","state":"SUCCESS","completedAt":"2026-01-01T00:00:00Z"}]')" = "success" ]
[ "$(bugbot_state '[{"name":"Linktrend Review Gate","state":"NEUTRAL","completedAt":"2026-01-01T00:00:00Z"}]')" = "not_success" ]
[ "$(bugbot_state '[{"name":"Linktrend Review Gate","state":"PENDING","completedAt":"2026-01-01T00:00:00Z"}]')" = "pending" ]
[ "$(bugbot_state '[{"name":"Verify IDE Development","state":"SUCCESS"}]')" = "missing" ]
[ "$(bugbot_state '[{"name":"Linktrend Review Gate","state":"SUCCESS","completedAt":"2026-01-01T00:00:00Z"},{"name":"Linktrend Review Gate","state":"NEUTRAL","completedAt":"2026-01-01T01:00:00Z"}]')" = "not_success" ]
[ "$(bugbot_state '[{"name":"Linktrend Review Gate","state":"NEUTRAL","completedAt":"2026-01-01T00:00:00Z"},{"name":"Linktrend Review Gate","state":"SUCCESS","completedAt":"2026-01-01T01:00:00Z"}]')" = "success" ]
[ "$(bugbot_state '[{"name":"Linktrend Review Gate","state":"SUCCESS","completedAt":"2026-01-01T01:00:00Z"},{"name":"Linktrend Review Gate","state":"CANCELLED","completedAt":"2026-01-01T00:00:00Z"}]')" = "success" ]
echo "PASS: integrator Bugbot gate cases"
