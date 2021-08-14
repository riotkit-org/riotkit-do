Task Inheritance
----------------



InputOutput
-----------

Every Task has its own instance of `IO`. Task compilation, context preparation stages are using `SystemIO`, so the 
`IO` configuration is having settings defined with commandline switches **before first task**.

**Reasons:**
- Each task can have different logging level
- Each task can log to different file (even cannot write to same file)
- Task has separate IO settings than RKD global UI
- `--no-ui` before first task disables RKD interface messages like `Successfully executed 2 tasks` but keeps interface produced by Task eg. `>> chown www-data:www-data /tmp/script.php`
- `--silent` before first task disables ALL interfaces both RKD and produced by Task. Only necessary messages are print

**Global logging level - before first task examples**

```bash
./rkdw --no-ui :first-task :second-task

# defines log level on very early stage, before arguments parsing. Can be set to any level including debug, info, warning, error
# "internal" is a level that contains internal RKD core debugging messages. Warning: There could be a lot of messages
# use "debug" to debug your tasks
RKD_SYS_LOG_LEVEL=internal ./rkdw :first-task :second-task
```

**Logging levels:**
- internal: Includes RKD core internal messages
- debug: Includes task-related debugging messages
- info: User info messages
- warning: Warnings
- error: Errors
- fatal: Fatal errors
