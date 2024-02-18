import html
import json
import xml.etree.ElementTree as ET
import os
from prettytable import PrettyTable
import re

class Colors:
    HEADER = '\033[96m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

logo = """
 _   _                                            
| | | |                                           
| |_| |  __ _  _ __  _ __    ___  ___  ___        
|  _  | / _` || '__|| '_ \  / _ \/ __|/ __|       
| | | || (_| || |   | | | ||  __/\__ \\__ \       
\_| |_/ \__,_||_|   |_| |_| \___||___/|___/       
                                                  
                                                  
 _____                           _  _             
/  ___|                         (_)| |            
\ `--.   ___  _ __   ___  _ __   _ | |_  _   _    
 `--. \ / _ \| '__| / _ \| '_ \ | || __|| | | |   
/\__/ /|  __/| |   |  __/| | | || || |_ | |_| |   
\____/  \___||_|    \___||_| |_||_| \__| \__, |   
                                          __/ |   
                                         |___/    
 _____                            _               
|  ___|                          | |              
| |__  __  __ _ __    ___   _ __ | |_   ___  _ __ 
|  __| \ \/ /| '_ \  / _ \ | '__|| __| / _ \| '__|
| |___  >  < | |_) || (_) || |   | |_ |  __/| |   
\____/ /_/\_\| .__/  \___/ |_|    \__| \___||_|   
             | |                                  
             |_|                                  
"""

developer_name = "Developed by: Diego Paes Ramalho Pereira"

def colorize(text, color):
    return f"{color}{str(text)}{Colors.ENDC}"

def colorize_multiline(text, color):
    """
    Applies ANSI color codes to each line in a multi-line string.
    """
    colored_lines = [f"{color}{line}{Colors.ENDC}" for line in text.split('\n')]
    return '\n'.join(colored_lines)

# Error table initializer
failure_table = PrettyTable()
error_table = PrettyTable()
# 
failure_table.field_names = ["Test Case", "Message", "Stack Trace"]
error_table.field_names = ["Test Case", "Message", "Stack Trace"]
# add a title Failures
failure_table.title = "Failures"
error_table.title = "Errors"
# align the table to the left
failure_table.align = "l"
error_table.align = "l"
# set width for the table
failure_table.min_width["Test Case"] = 73
failure_table.min_width["Message"] = 73
failure_table.min_width["Stack Trace"] = 120
failure_table.max_width["Test Case"] = 73
failure_table.max_width["Message"] = 73
failure_table.max_width["Stack Trace"] = 120

error_table.min_width["Test Case"] = 73
error_table.min_width["Message"] = 73
error_table.min_width["Stack Trace"] = 120
error_table.max_width["Test Case"] = 73
error_table.max_width["Message"] = 73
error_table.max_width["Stack Trace"] = 120



# Initialize counters
total_tests = 0
total_failures = 0
total_errors = 0
total_failure_errors = 0
separator = f"\033[34m-----------------------------------------------------------------\033[0m"

def sanitize_for_xml(input_text):
    """
    Removes characters that are illegal in XML.
    """
    # Regex to match illegal XML characters
    illegal_xml_chars_re = re.compile(u'[\u0000-\u0008\u000b-\u000c\u000e-\u001f\u007f-\u0084\u0086-\u009f]')
    sanitized_text = re.sub(illegal_xml_chars_re, '', input_text)
    return sanitized_text

def create_test_case_element(testsuite, name, duration, result, error_info=None):
    """Creates a testcase element with potential failure or error."""
    global total_tests, total_failures, total_errors, total_failure_errors, separator, failure_table, error_table

    sanitized_name = sanitize_for_xml(name)
    testcase = ET.SubElement(testsuite, 'testcase', attrib={'name': sanitized_name, 'time': str(duration)})
    total_tests += 1
    
    # For failures, use the 'testFailureMessage' and append the last stack trace element.
    if result == "FAILURE":
        total_failures += 1
        total_failure_errors += 1
    # For errors, use the 'message' from the 'exception' field and append the last stack trace element.
    elif result == "ERROR":
        total_errors += 1
        total_failure_errors += 1
    
    failure_message = error_info['message'] if error_info and 'message' in error_info else "Test failed" if result == "FAILURE" else "Test encountered an error"

    if error_info and 'stackTrace' in error_info:
        # Get the last item from the stack trace
        last_stack_trace = error_info['stackTrace'][-1]
        full_stack_trace = format_stack_trace(error_info['stackTrace'])
        # Adjusted table structure to include detailed information
        
        failure_table.add_row([sanitized_name, colorize_multiline(failure_message, Colors.WARNING) , colorize_multiline(full_stack_trace, Colors.FAIL )]) if result == "FAILURE" else error_table.add_row([sanitized_name, colorize_multiline(failure_message, Colors.WARNING) , colorize_multiline(full_stack_trace, Colors.FAIL )])

        class_method = f"{last_stack_trace.get('declaringClass', 'Unknown')}.{last_stack_trace.get('methodName', 'method')}"
        file_name = f"({last_stack_trace.get('fileName', 'Unknown')})"
        file_line = f"({last_stack_trace.get('lineNumber', 'Unknown')})"
        # Append the last stack trace to the failure message
        # verify if env var "PLUGIN_FULL_STACK_TRACE" is set to true and change failure message
        failure_message += f"\nLast stack trace:\n {class_method} \n \nFile: {file_name} \nLine Nummber:{file_line}"
        failure_message = f"{failure_message}\n{class_method} {file_name} {file_line}\n{separator}\n{full_stack_trace}" if os.environ.get('PLUGIN_FULL_STACK_TRACE', 'false').lower() == 'true' else failure_message
    if result != "SUCCESS":
        failure_message = sanitize_for_xml(failure_message)
        failure = ET.SubElement(testcase, 'failure', attrib={'message': failure_message, 'type': "failure"})


def format_stack_trace(stack_trace):
    """Formats the stack trace for XML output."""
    stack_trace_elements = []
    for element in stack_trace:
        class_method = f"{element.get('declaringClass', 'Unknown')}.{element.get('methodName', 'method')}"
        file_line = f"({element.get('fileName', 'Unknown')}:{element.get('lineNumber', 'Unknown')})"
        stack_trace_elements.append(f"\nat {class_method} {file_line}")
    return "\n".join(stack_trace_elements)

def process_json_file(json_file, root):
    with open(json_file) as f:
        data = json.load(f)

    if os.getenv('PLUGIN_DEBUG', 'false') == "true":
        #show json content
        print(f"\033[34mProcessing file: {json_file}\033[0m")

    test_case_name = data.get('testCaseName', data.get('scenarioId', 'UnnamedTestCase'))
    # debuf test case name if UnnamedTestCase
    if test_case_name == 'UnnamedTestCase':
        print(f"\033[34mDEBUG: UnnamedTestCase found in {json_file}\033[0m")
        # print json content first level content keys and values
        first_level_keys = data.keys()
        first_level_values = data.values()
        print(first_level_keys)
        print(first_level_values)

    method_name = data.get('methodName', 'UnnamedMethod')  # Fallback for methodName

    testsuite_name = data.get('name', 'UnnamedTest')
    testsuite = ET.SubElement(root, 'testsuite', name=testsuite_name, tests=str(len(data['dataTable']['rows'])) if 'dataTable' in data and data['dataTable'].get('rows') else "1")
    
    # set duration to json root duration in seconds
    duration = data.get('duration', 0) / 1000.0

    # duration = sum(step['duration'] for step in data.get('testSteps', [])) / 1000.0
    result = data.get('result', 'UNKNOWN')
    if os.getenv('PLUGIN_DEBUG', 'false') == "true":
        print(f"\033[34mProcessing test case: {test_case_name}, Result: {result}\033[0m")

    if 'dataTable' in data and data['dataTable'].get('rows'):
        
        for row in data['dataTable']['rows']:
            row_values = ', '.join(row['values'])
            test_name = f"{method_name} {row_values} - {test_case_name}"
            result = row.get('result', 'UNKNOWN')
            if os.getenv('PLUGIN_DEBUG', 'false') == "true":
                print(f"\033[34mDEBUG: Processing parameterized test case: {test_name}, Result: {result}\033[0m")
            # check results is UNDEFINED skip
            if result != "UNDEFINED":
                # duration is divded by the number of rows excluding from rows count with result = "UNDEFINED"
                new_row_count = len(data['dataTable']['rows']) - len([row for row in data['dataTable']['rows'] if row.get('result', 'UNKNOWN') == "UNDEFINED"])
                new_duration = sum(step['duration'] for step in data.get('testSteps', [])) / 1000.0 / new_row_count
                
                create_test_case_element(testsuite, test_name, new_duration, result, data.get('testFailureCause') if result != "SUCCESS" else None)
    else:
        test_name = f"{method_name} - {test_case_name}"
        if os.getenv('PLUGIN_DEBUG', 'false') == "true":
            print(f"\033[34mDEBUG: Processing single test case: {test_name}, Result: {data.get('result', 'UNKNOWN')}\033[0m")
        create_test_case_element(testsuite, test_name, duration, result, data.get('testFailureCause') if result != "SUCCESS" else None)

def generate_junit_report(directory, output_file):
    global separator, error_table, failure_table, total_tests, total_failures, total_errors, total_failure_errors
    root = ET.Element('testsuites')
    
    for file_name in os.listdir(directory):
        if file_name.endswith('.json'):
            process_json_file(os.path.join(directory, file_name), root)

    tree = ET.ElementTree(root)

    tree.write(output_file, encoding='utf-8', xml_declaration=True)

    # Calculate failure rate
    failure_rate = (total_failure_errors / total_tests * 100) if total_tests > 0 else 0

    if total_failure_errors > 0:
        print(failure_table)
    if total_errors > 0:
        print(error_table)


    # Output statistics with PrettyTable and ANSI colors
    summary_table = PrettyTable()
    summary_table.field_names = ["Metric", "Value"]
    summary_table.title = "Test Summary"
    summary_table.header = False
    summary_table.add_row(["Total tests", colorize(total_tests, Colors.OKGREEN)])
    summary_table.add_row(["Total errors+failures", colorize(total_failure_errors, Colors.FAIL) if total_failure_errors > 0 else colorize(total_failure_errors, Colors.OKGREEN)])
    summary_table.add_row(["Failure rate", colorize(f"{failure_rate if total_tests > 0 else 0:.2f}%", Colors.WARNING)])
    summary_table.min_width = 30
    # align the table to the right but only first column
    summary_table.align["Metric"] = "r"
    summary_table.align["Value"] = "l"

    print(summary_table)

    # Create tables
    error_details_table = PrettyTable()
    failure_details_table = PrettyTable()
    threshold_table = PrettyTable()

    # Configure tables
    error_details_table.title = colorize("Errors",Colors.FAIL)
    error_details_table.field_names = ["Type", "Count"]
    error_details_table.min_width = 30
    # remove the columns name
    error_details_table.header = False
    error_details_table.align["Type"] = "r"
    error_details_table.align["Count"] = "l"

    failure_details_table.field_names = ["Type", "Count"]
    failure_details_table.title = colorize("Failures",Colors.FAIL)
    # remove the columns name
    failure_details_table.header = False
    failure_details_table.align["Type"] = "r"
    failure_details_table.align["Count"] = "l"
    failure_details_table.min_width = 30

    threshold_table.field_names = ["Threshold", "Failure Rate", "Status"]
    # threshold_table.align = "l"
    threshold_table.min_width = 19

    # Output errors and failures details if any
    if total_failures > 0:
        # Assuming total_failures, total_errors, and failure_rate are defined
        failure_details_table.add_row([ colorize("Total Failures",Colors.FAIL) , colorize(total_failures,Colors.FAIL)])
        print(failure_details_table)
    if total_errors > 0:
        error_details_table.add_row([colorize("Total Errors",Colors.FAIL), colorize(total_errors,Colors.FAIL)])
        print(error_details_table)

    threshold = float(os.environ.get('PLUGIN_THRESHOLD', '0'))  # Default to 100 if not set
    status = colorize("PASSED",Colors.OKGREEN) if failure_rate <= threshold else colorize("FAILED",Colors.FAIL)
    threshold_table.add_row([colorize(f"{threshold}%",Colors.WARNING) , colorize(f"{failure_rate:.2f}%",Colors.OKGREEN) if failure_rate <= threshold else colorize(f"{failure_rate:.2f}%",Colors.FAIL) , status])

    # Prepare your environment variables for writing to the .env file
    env_variables = {
        "TOTAL_TESTS": str(total_tests),
        "TOTAL_FAILURES": str(total_failures),
        "TOTAL_ERRORS": str(total_errors),
        "TOTAL_ERRORS_FAILED": str(total_failure_errors),
        "FAILURE_RATE": str(failure_rate),
        "FAILURES_TESTS_OUTPUT": failure_table, #.replace("\n", ""),
        "ERRORS_TESTS_OUTPUT": error_table #.replace("\n", ""),
    }

    # Specify the path to your .env file
    file_path = os.getenv('DRONE_OUTPUT', 'default_env_file.env')

    # Call the function to write the environment variables to the .env file
    write_env_file(env_variables, file_path)
    
    threshold_table.title = f"Acceptance Threshold Check"
    print(threshold_table)
    
    # #check if THESHOLD env var is set and not empty, then check the theshould agains failure rate
    if os.environ.get('PLUGIN_THRESHOLD', ''):
        threshold = float(os.environ.get('PLUGIN_THRESHOLD', ''))
        if failure_rate > threshold:
            exit(1)
        else:
            exit(0)

# Function to write environment variables to the .env file
def write_env_file(variables, file_path):
    try:
        with open(file_path, 'w') as f:
            for key, value in variables.items():
                f.write(f"{key}={value}\n")
    except IOError as e:
        print(f"Error writing to .env file: {e}")

if __name__ == '__main__':
    print(colorize_multiline(logo, Colors.HEADER))
    print(colorize(developer_name, Colors.OKGREEN))
    print(separator)
    # check if env var "PLUGIN_SERENITY_REPORT_DIR" is set and not empty, then use it as directory
    directory = os.environ.get('PLUGIN_SERENITY_REPORT_DIR', 'target/site/serenity/')  # Update this path to your directory containing JSON files
    # if it end with .xml .json or .html show a error message saying that value it is not a directory and we will use the default value
    if directory.endswith('.xml') or directory.endswith('.json') or directory.endswith('.html'):
        print(f"\033[31mERROR: {directory} is not a directory, using default value: target/site/serenity/\033[0m")
        directory = 'target/site/serenity/'
    # check if it ends with /, if not add it
    if not directory.endswith('/'):
        directory = f"{directory}/"
    output_file = 'serenity_junit_output.xml'
    generate_junit_report(directory, output_file)
