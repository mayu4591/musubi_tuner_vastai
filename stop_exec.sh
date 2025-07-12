#!/bin/bash

# execute_sh.py のPIDを取得
execute_sh_pid=$(ps -ef | grep "run_train.sh" | grep -v grep | awk '{print $2}')

# execute_sh_pidの子プロセスを再帰的に取得してKILL
kill_process() {
    local pid=$1
    local child_pids=$(pgrep -P $pid)

    for child_pid in $child_pids; do
        kill_process $child_pid
    done

    # プロセスを強制終了
    kill -9 $pid
}

# execute_sh.pyのPIDを強制終了
if [ -n "$execute_sh_pid" ]; then
    kill_process $execute_sh_pid
    echo "Stopped execute_sh.py with PID: $execute_sh_pid"
else
    echo "No run_train.sh process found."
fi