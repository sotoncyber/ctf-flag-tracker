#!/usr/bin/env bash
tracker_path="/opt/tracker"
if [ -f "$tracker_path/venv/bin/python3" ]; then
    $("$tracker_path/venv/bin/python3" <<EOF
import os
os.chdir('$tracker_path')
import tracker
with tracker.app.app_context():
    u = tracker.user.get_user('$1')
    u.set_admin(True)
EOF
    )
    RES=$?
else
    $("./venv/bin/python3" <<EOF
import tracker
with tracker.app.app_context():
    u = tracker.user.get_user('$1')
    u.set_admin(True)
EOF
    )
    RES=$?
fi
if [ "$RES" -eq 0 ]; then
    echo "Set admin privs for $1"
else
    echo "Failed to set admin privs for $1"
fi