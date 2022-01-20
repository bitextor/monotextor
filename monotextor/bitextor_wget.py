#!/usr/bin/env python3

#  This file is part of Bitextor.
#
#  Bitextor is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Bitextor is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Bitextor.  If not, see <https://www.gnu.org/licenses/>.

import argparse
import subprocess
import sys
import requests
import time

from warcio.archiveiterator import ArchiveIterator
from warcio.warcwriter import WARCWriter
from warcio.statusandheaders import StatusAndHeaders
from monotextor.utils.common import check_connection


def system_check(cmd):
    sys.stderr.write("Executing:" + cmd + "\n")
    sys.stderr.flush()

    subprocess.check_call(cmd, shell=True)


def check_wget_compression(cmd):
    try:
        subprocess.check_call(cmd, shell=True, stdout=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False


def run(url, out_path, time_limit, agent, filetypes, warcfilename, wait):
    cmd = ""
    if time_limit:
        cmd += "timeout {} ".format(time_limit)
    waitoption = ""
    if wait is not None:
        waitoption = "--wait " + wait
    agentoption = ""
    if agent is not None:
        agentoption = "--user-agent \"" + agent + "\""

    filetypesoption = ""
    if filetypes is not None:
        filetypesoption = "-A \"" + filetypes + "\""

    warcoption = ""
    warcfilebasename = warcfilename[0:warcfilename.find(".warc.gz")]
    if warcfilename is not None:
        warcoption = "--warc-file \"" + warcfilebasename + "\""

    if check_wget_compression("wget --help | grep 'no-warc-compression'"):
        warcoption += " --no-warc-compression"

    cmd += f"wget --mirror {waitoption} {filetypesoption} -q -o /dev/null {url} -P {out_path} {agentoption} {warcoption}"

    start_time = time.time()

    try:
        system_check(cmd)
    except subprocess.CalledProcessError as grepexc:
        suffix = f" (return code: {grepexc.returncode})"

        if time_limit and grepexc.returncode == 124:
            suffix = " (timeout)"

        sys.stderr.write(f"WARNING: some files could not be downloaded with wget{suffix}\n")

    print(f"The crawling took {time.time() - start_time:.0f} seconds")

    with open(warcfilebasename + ".warc", 'rb') as f_in:
        with open(warcfilebasename + ".warc.gz", 'wb') as f_out:
            writer = WARCWriter(f_out, gzip=True)
            try:
                for record in ArchiveIterator(f_in):
                    if record.http_headers:
                        try:
                            record.http_headers.to_ascii_bytes()
                        except UnicodeEncodeError:
                            # if header is non ascii, create a new header, with status code only
                            # content length and content type will be filled before writing
                            record.http_headers = StatusAndHeaders(record.http_headers.get_statuscode(), [])
                    uri = record.rec_headers.get_header('WARC-Target-URI')
                    # ignore metadata records
                    if not uri or uri.startswith('metadata://gnu.org/software/wget/warc/'):
                        continue
                    record.length = None
                    writer.write_record(record)
            except Exception as e:
                print(e, file=sys.stderr)
                pass

    system_check("rm {WARC}".format(WARC=warcfilebasename + ".warc"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Run wget.')

    parser.add_argument('--url', dest='url',
                        help='Domain to crawl', required=True)
    parser.add_argument('--output-path', dest='outPath',
                        help='Directory to write to', required=True)
    parser.add_argument('-t', dest='timeLimit',
                        help='Maximum time to crawl.', required=False)
    parser.add_argument('-a', dest='agent',
                        help='User agent to be included in the crawler requests.', required=False, default=None)
    parser.add_argument('-f', dest='filetypes',
                        help='File types to be downloaded, comma separated. For example, "html,pdf"', required=False,
                        default=None)
    parser.add_argument('--warc', dest='warcfilename',
                        help='Write output to a WARC file', required=False, default=None)
    parser.add_argument('--wait', dest='wait',
                        help='Wait N seconds between queries', required=False, default=None)

    args = parser.parse_args()

    print("Starting...")

    if '//' not in args.url:
        args.url = '%s%s' % ('http://', args.url)

    connection_error, fixed_url = check_connection(args.url)

    if not connection_error:
        args.url = fixed_url

        try:
            robots = requests.get(args.url + "/robots.txt", timeout=15).text.split("\n")
            for line in robots:
                if "Crawl-delay" in line:
                    try:
                        crawldelay = int(line.split(':')[1].strip())
                        if args.wait is None or crawldelay > int(args.wait):
                            args.wait = str(crawldelay)
                    except ValueError:
                        pass
        except BaseException as e:
            sys.stderr.write("WARNING: error downloading robots.txt\n")
            sys.stderr.write(str(e) + "\n")

        run(args.url, args.outPath, args.timeLimit, args.agent, args.filetypes, args.warcfilename, args.wait)
    else:
        # Create empty warc
        warc_file_basename = args.warcfilename[0:args.warcfilename.find(".warc.gz")]

        with open(warc_file_basename + ".warc.gz", 'w') as f_out:
            f_out.close()

    print("Finished!")
