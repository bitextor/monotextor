import sys
import re

email_regex = r"(\b|^)([a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*)(\b|$)"
phone_regex = r"(?![\-\–\(]?\s*\d{2,4}\s*[\-\–\s]\s*\d{3,4}\s*[\-\–\(]?)[\+\-\–\(\d].[\(\)' '\+\-\–\d]{6,12}\d{2}\b"
IPv4_regex = r"((?:[0-9]{1,3}\.){3}[0-9]{1,3})"
IPv6_regex = r"(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))"


all_regex = re.compile(r"(" + email_regex + r")|(" + phone_regex +r")|(" + IPv4_regex + r")|(" + IPv6_regex + r")")

for line in sys.stdin:
    line_strip = line.rstrip()
    text = line_strip.split('\t')[1]
    match = all_regex.search(text)
    if match is None:
        print(line_strip, 'no', sep='\t')
    else:
        print(line_strip, 'yes', sep='\t')
        #print(match, line, file=sys.stderr)
