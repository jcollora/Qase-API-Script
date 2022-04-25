import qaseio.client
from qaseio.client import QaseApi
from qaseio.client.models import TestRunCreate, TestRunResultCreate, TestRunResultStepCreate, TestRunResultStatus

# NOTE: minimal error checking in prompt, improper case_ids or will lead to crash

# use a token from https://app.qase.io/user/api/token
qase = QaseApi("*token here")

while 1:
    prjcode = input('Project Code: ')
    if qase.projects.exists(prjcode):
        break
    else:
        print('ERR: Specified project does not exist.')

# dual function script. create results or a new run?
dualswitch = input('Test Run = \'T\', Result = \'R\', Both = \'B\': ')
if dualswitch.lower() == 'r' or dualswitch.lower() == 'b':
    results = True
else:
    results = False

# NOTE: API does not allow for setting milestone or plan ids
# =================================================================
#                         Run Creation
# =================================================================
if not results:
    title = input('Run Title: ')
    descr = input('Description (<1k chars): ')
    environment_id = input('Environment ID: ')

    cases_raw = input('Enter case #s separated by a " ": ')
    case_list = [int(x) for x in cases_raw.split()]

    if environment_id != '':
        environment_id = int(environment_id)
        test_run = qase.runs.create(
            prjcode,
            TestRunCreate(title=title,
                          cases=case_list,
                          description=descr,
                          environment_id=environment_id),
        )
    else:
        test_run = qase.runs.create(
            prjcode,
            TestRunCreate(title=title,
                          cases=case_list,
                          description=descr),
        )


# switch for if both operations desired
if dualswitch.lower() == 'b':
    results = True

# =================================================================
#                        Result Creation
# =================================================================
# Get the testrun, in each case get the steps and prompt user

if results:
    run_id = input('Testrun ID: ')
    casenum = input('Case Number: ')

    if qase.runs.exists(prjcode, run_id):
        # The run object is obtained
        # Look inside to see its unique cases
        test_run = qase.runs.get(prjcode, run_id)

    # get target case to for-each
    test_case = qase.cases.get(prjcode, casenum)

    # instantiate list
    step_list = []
    # position counter for steps
    count = 1

    # until case has a failed step, it passes
    case_passed = True

    # create each step with loop
    for x in test_case.steps:
        prompt = 'Step #' + str(count) + ' passed "p" or fail "f" : '
        step_status = input(prompt)

        if step_status.lower() == 'p':
            status = 'passed'
        else:
            # if one-step fails, the case is considered a failure
            status = TestRunResultStatus.FAILED
            case_passed = 'failed'

        comments = input('Please type comments for this result: ')
        step_list.append(TestRunResultStepCreate(position=count,
                                                 status=status,
                                                 comment=comments))
        count = count + 1

    # use api call to create a new result that includes the case
    # status in addition to the individual steps

    qase.results.create(prjcode,
                        run_id,
                        TestRunResultCreate(casenum,
                                            case_passed,
                                            steps=step_list))
    S