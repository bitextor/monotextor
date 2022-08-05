#!/bin/bash

DIR="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
source $DIR/common.sh

exit_program()
{
  >&2 echo "$1 [-w workdir] [-f force_command] [-j threads]"
  >&2 echo ""
  >&2 echo "Runs several tests to check Monotextor is working"
  >&2 echo ""
  >&2 echo "OPTIONS:"
  >&2 echo "  -w <workdir>            Working directory. By default: \$HOME"
  >&2 echo "  -f <force_command>      Options which will be provided to snakemake"
  >&2 echo "  -j <threads>            Threads to use when running the tests"
  exit 1
}

WORK="${HOME}"
WORK="${WORK/#\~/$HOME}" # Expand ~ to $HOME
FORCE=""
THREADS=1

while getopts "hf:w:j:" i; do
    case "$i" in
        h) exit_program "$(basename "$0")" ; break ;;
        w) WORK=${OPTARG};;
        f) FORCE="--${OPTARG}";;
        j) THREADS="${OPTARG}";;
        *) exit_program "$(basename "$0")" ; break ;;
    esac
done
shift $((OPTIND-1))

MONOTEXTOR="monotextor-full ${FORCE} --notemp -j ${THREADS} -c ${THREADS} --reason"
FAILS="${WORK}/data/fails.log"
mkdir -p "${WORK}"
mkdir -p "${WORK}/permanent"
mkdir -p "${WORK}/transient"
mkdir -p "${WORK}/data"
mkdir -p "${WORK}/data/warc"
mkdir -p "${WORK}/reports"
rm -f "$FAILS"
touch "$FAILS"

# Download necessary files
# WARCs
download_file "${WORK}/data/warc/greenpeace.warc.gz" https://github.com/bitextor/bitextor-data/releases/download/bitextor-warc-v1.1/greenpeace.canada-small.warc.gz &
wait

# MT (id >= 10)
(
    init_test "10"

    ${MONOTEXTOR} \
        --config profiling=True permanentDir="${WORK}/permanent/${TEST_ID}" \
            dataDir="${WORK}/data/${TEST_ID}" transientDir="${WORK}/transient/${TEST_ID}" \
            warcs="['${WORK}/data/warc/greenpeace.warc.gz']" preprocessor="warc2text" shards=0 batches=99999 \
            langs="['en', 'fr']" paragraphIdentification=True skipSentenceSplitting=True \
        &> "${WORK}/reports/${TEST_ID}.report"

    finish_test "en fr" "raw.paragraphs.gz"
) &

wait

# Results
failed=$(cat "$FAILS" | wc -l)

echo "------------------------------------"
echo "           Fails Summary            "
echo "------------------------------------"
echo "status | test-id | exit code / desc."
cat "$FAILS"

exit "$failed"
