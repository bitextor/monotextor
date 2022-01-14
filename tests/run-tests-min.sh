#!/bin/bash

DIR="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
source $DIR/common.sh

exit_program()
{
  >&2 echo "$1 [-w workdir] [-f force_command] [-j threads]"
  >&2 echo ""
  >&2 echo "Runs several tests to check Bitextor is working"
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

MONOTEXTOR="monotextor"
MONOCLEANER="${WORK}/monocleaner-model"
FAILS="${WORK}/data/fails.log"
mkdir -p "${WORK}"
mkdir -p "${WORK}/reports"
mkdir -p "${MONOCLEANER}"
mkdir -p "${WORK}/data/warc"
mkdir -p "${WORK}/data/warc/clipped"
mkdir -p "${WORK}/data/parallel-corpus"
mkdir -p "${WORK}/data/parallel-corpus/Europarl"
mkdir -p "${WORK}/data/parallel-corpus/DGT"
rm -f "$FAILS"
touch "$FAILS"

# Download necessary files
# WARCs
download_warc "${WORK}/data/warc/greenpeace.warc.gz" https://github.com/bitextor/bitextor-data/releases/download/bitextor-warc-v1.1/greenpeace.canada.warc.gz &
# Bicleaner models
download_monocleaner_model "en" "${MONOCLEANER}" &
download_monocleaner_model "fr" "${MONOCLEANER}" &
wait

### WARC clipped
if [ ! -f "${WORK}/data/warc/clipped/greenpeaceaa.warc.gz" ]; then
    ${DIR}/split-warc.py -r 1000 "${WORK}/data/warc/greenpeace.warc.gz" "${WORK}/data/warc/clipped/greenpeace" &
fi

wait

# Remove unnecessary clipped WARCs
ls "${WORK}/data/warc/clipped/" | grep -v "^greenpeaceaa[.]" | xargs -I{} rm "${WORK}/data/warc/clipped/{}"
# Rename and link
mv "${WORK}/data/warc/greenpeace.warc.gz" "${WORK}/data/warc/greenpeace.original.warc.gz"
ln -s "${WORK}/data/warc/clipped/greenpeaceaa.warc.gz" "${WORK}/data/warc/greenpeace.warc.gz"

# MT (id >= 10)
(
    ${MONOTEXTOR} ${FORCE} --notemp -j ${THREADS} \
        --config profiling=True permanentDir="${WORK}/permanent/monotextor-output-en-and-fr" \
            dataDir="${WORK}/data/data-en-and-fr" transientDir="${WORK}/transient-en-and-fr" \
            warcs="['${WORK}/data/warc/greenpeace.warc.gz']" preprocessor="warc2text" shards=0 batches=99999 langs="['en', 'fr']" \
            monocleaner=True monofixer=True \
	    monocleanerModels="{'en': '${MONOCLEANER}/en/', 'fr': '${MONOCLEANER}/fr/'}"\
        &> "${WORK}/reports/10-en--and-fr.report"
    annotate_and_echo_info 10 "$?" "$(get_nolines ${WORK}/permanent/monotextor-output-en-and-fr/en.sent.gz)"
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
