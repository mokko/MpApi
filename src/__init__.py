def mink():
    import argparse

    with open(credentials) as f:
        exec(f.read())

    parser = argparse.ArgumentParser(description="Commandline frontend for MpApi.py")
    parser.add_argument("-j", "--job", help="job to run", required=True)
    parser.add_argument("-c", "--conf", help="config file", default="jobs.dsl")
    args = parser.parse_args()

    m = Mink(job=args.job, conf=args.conf, baseURL=baseURL, pw=pw, user=user)
