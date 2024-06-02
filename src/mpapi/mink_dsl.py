"""
Let's improve the dsl parser...

Work in progress

todo:
- definte errors, probably a ConfigError

if config file has no job at all
if config file has same job multiple time
if more than two indent levels
if active job doesn't exist
if active job has no commands

job:
    command with multiple parts
    multiple commands in order # can have comments
# comments can begin anywhere, even at the beginning of the line
job: # not allowed to specify same job twice
    command
        subcommand # currently only two levels allowed
"""
def parse_dsl(conf_fn:Path, job:str) -> list[str]:
    """
    Return the part of the configuration that refers to job. Do we really rely 
    on order?

    as a list:
        conf = ["chunk group 12345", "getPack group 12345"]

    We also considered a dict format, but since we dont need it right now, let'seek
    not do that at the moment.
    """
    any_job: bool = False
    known_jobs = list()
    commands = list()
    with open(conf_fn, mode="r") as file:
        for c, line in enumerate(file, start=1):
        uncomment = line.split("#", 1)[0].strip()
        if uncomment.isspace() or not uncomment:
            continue
        line = line.expandtabs(4)
        indent_lvl = int((len(line) - len(line.lstrip()) + 4) / 4)
        parts: list[str] = uncomment.split()
        if indent_lvl == 1:  # job label
            if not parts[0].endswith(":"):
                raise SyntaxError(
                    f"Job label has to end with colon: line {c} {parts[0]}"
                )
            current_job = parts[0][:-1]
            known_jobs.append(current_job)
            if current_job == job:
                right_job = True
                any_job = True
            else:
                right_job = False
            #continue
        elif indent_lvl == 2:
            if right_job is True:
                commands.append(uncomment)
                else:
                    raise SyntaxError(f"ERROR: Command '{cmd}' not recogized")
        elif indent_lvl > 2:
            print(f"indent lvl: {indent_lvl} {parts}")
            raise SyntaxError("ERROR: Too many indents in dsl file")
    return commands
