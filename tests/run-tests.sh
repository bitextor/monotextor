#!/bin/bash
DIR="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
source $DIR/common.sh

exit_program()
{
  >&2 echo "$1 [-w <workdir>] [-f <force_command>] [-j <threads>] [-t <tests>]"
  >&2 echo ""
  >&2 echo "Runs several tests to check Monofixer is working"
  >&2 echo ""
  >&2 echo "OPTIONS:"
  >&2 echo "  -w <workdir>            Working directory. By default: \$HOME"
  >&2 echo "  -f <force_command>      Options which will be provided to snakemake"
  >&2 echo "  -j <threads>            Threads to use when running the tests"
  >&2 echo "  -t <tests>              Tests which will be executed. The way they are"
  >&2 echo "                            specified is similar to 'chmod'. The expected format"
  >&2 echo "                            is numeric (e.g. 2 means to run the 2nd function of"
  >&2 echo "                            tests, 4 means to run the 3rd function of tests, 3"
  >&2 echo "                            means to run the 2nd and 3rd function of tests). Hex"
  >&2 echo "                            numbers can also be provided. By default: 2^32-1,"
  >&2 echo "                            which means running all the tests"
  >&2 echo "  -n                      Dry run. Do not execute anything, only show which tests"
  >&2 echo "                            will be executed."

  exit 1
}

WORK="${HOME}"
WORK="${WORK/#\~/$HOME}" # Expand ~ to $HOME
FORCE=""
THREADS=1
FLAGS="$(echo 2^32-1 | bc)"
DRYRUN=false

while getopts "hf:w:j:t:n" i; do
    case "$i" in
        h) exit_program "$(basename "$0")" ; break ;;
        w) WORK=${OPTARG};;
        f) FORCE="--${OPTARG}";;
        j) THREADS="${OPTARG}";;
        t) FLAGS="${OPTARG}";;
        n) DRYRUN=true;;
        *) exit_program "$(basename "$0")" ; break ;;
    esac
done
shift $((OPTIND-1))

MONOTEXTOR="monotextor-full ${FORCE} --notemp -j ${THREADS} -c ${THREADS} --reason"
MONOTEXTOR_EXTRA_ARGS="profiling=True"
MONOCLEANER="${WORK}/data/monocleaner-models"
FAILS="${WORK}/data/fails.log"
mkdir -p "${WORK}"
mkdir -p "${WORK}/permanent"
mkdir -p "${WORK}/transient"
mkdir -p "${WORK}/data/warc"
mkdir -p "${WORK}/data/parallel-corpus"
mkdir -p "${WORK}/data/prevertical"
mkdir -p "${WORK}/reports"
mkdir -p "${MONOCLEANER}"
rm -f "$FAILS"
touch "$FAILS"

# Download necessary files
# WARCs
download_file "${WORK}/data/warc/greenpeace.warc.gz" https://github.com/bitextor/bitextor-data/releases/download/bitextor-warc-v1.1/greenpeace.canada.warc.gz &
download_file "${WORK}/data/warc/primeminister.warc.gz" https://github.com/bitextor/bitextor-data/releases/download/bitextor-warc-v1.1/primeminister.warc.gz &
download_file "${WORK}/data/warc/kremlin.warc.gz" https://github.com/bitextor/bitextor-data/releases/download/bitextor-warc-v1.1/kremlin.warc.gz &
# Monocleaner models
download_monocleaner_model "en" "${MONOCLEANER}" &
download_monocleaner_model "fr" "${MONOCLEANER}" &
download_monocleaner_model "el" "${MONOCLEANER}" &

wait

wait-if-envvar-is-true()
{
    value="$CI"

    if [[ "$1" != "" ]]; then
        if [[ "$(eval echo \$$1)" != "" ]]; then
            value=$(eval echo \$$1)
        fi
    fi

    if [[ "$value" == "true" ]]; then
        wait # wait before starting and finishing a test

        return 0
    else
        return 1
    fi
}

create-p2t-from-warc()
{
    if [[ ! -f "${WORK}/data/prevertical/greenpeace.en.prevertical.gz" ]] || \
       [[ ! -f "${WORK}/data/prevertical/greenpeace.fr.prevertical.gz" ]]; then
        mkdir -p "${WORK}/data/tmp-w2t"

        warc2text -o "${WORK}/data/tmp-w2t" -s -f "text,url" "${WORK}/data/warc/greenpeace.warc.gz" && \
        (
            python3 ${DIR}/utils/text2prevertical.py --text-files "${WORK}/data/tmp-w2t/en/text.gz" \
                --url-files "${WORK}/data/tmp-w2t/en/url.gz" --document-langs English --seed 1 \
            | pigz -c > "${WORK}/data/prevertical/greenpeace.en.prevertical.gz"
            python3 ${DIR}/utils/text2prevertical.py --text-files "${WORK}/data/tmp-w2t/fr/text.gz" \
                --url-files "${WORK}/data/tmp-w2t/fr/url.gz" --document-langs French --seed 2 \
            | pigz -c > "${WORK}/data/prevertical/greenpeace.fr.prevertical.gz" \
        )

        rm -rf "${WORK}/data/tmp-w2t"
    fi
}

# MT (id >= 10)
tests-mt()
{
    ## MT (en-fr)
    (
        init_test "10"

        ${MONOTEXTOR} ${FORCE} --notemp -j ${THREADS} \
            --config profiling=True permanentDir="${WORK}/permanent/${TEST_ID}" \
                dataDir="${WORK}/data/${TEST_ID}" transientDir="${WORK}/transient/${TEST_ID}" \
                warcs="['${WORK}/data/warc/greenpeace.warc.gz']" preprocessor="warc2text" shards=0 batches=99999 \
                langs="['en', 'fr']" paragraphIdentification=True monocleaner=True monofixer=True \
                monocleanerModels="{'en': '${MONOCLEANER}/en/', 'fr': '${MONOCLEANER}/fr/'}" \
                skipSentenceSplitting=True ${MONOTEXTOR_EXTRA_ARGS} \
            &> "${WORK}/reports/${TEST_ID}.report"

        finish_test "en fr" "raw.paragraphs.gz"
    ) &
    ## MT (en-el)
    (
        init_test "11"

        ${MONOTEXTOR} ${FORCE} --notemp -j ${THREADS} \
            --config profiling=True permanentDir="${WORK}/permanent/${TEST_ID}" \
                dataDir="${WORK}/data/${TEST_ID}" transientDir="${WORK}/transient/${TEST_ID}" \
                warcs="['${WORK}/data/warc/primeminister.warc.gz']" preprocessor="warc2text" shards=0 batches=99999 \
                langs="['en', 'el']" paragraphIdentification=True monocleaner=True monofixer=True \
                monocleanerModels="{'en': '${MONOCLEANER}/en/', 'el': '${MONOCLEANER}/el/'}" \
                skipSentenceSplitting=True ${MONOTEXTOR_EXTRA_ARGS} \
            &> "${WORK}/reports/${TEST_ID}.report"

        finish_test "en el" "raw.paragraphs.gz"
    ) &
}

# Other options (id >= 100)
tests-others()
{
    ## Disable all optional tools
    (
        init_test "100"

        ${MONOTEXTOR} ${FORCE} --notemp -j ${THREADS} \
            --config profiling=True permanentDir="${WORK}/permanent/${TEST_ID}" \
                dataDir="${WORK}/data/${TEST_ID}" transientDir="${WORK}/transient/${TEST_ID}" \
                warcs="['${WORK}/data/warc/greenpeace.warc.gz']" preprocessor="warc2text" shards=0 batches=99999 \
                langs="['en', 'fr']" paragraphIdentification=False monocleaner=False monofixer=False \
                skipSentenceSplitting=False ${MONOTEXTOR_EXTRA_ARGS} \
            &> "${WORK}/reports/${TEST_ID}.report"

        finish_test "en fr" "sent.gz"
    ) &
}

run-tests()
{
    flags="$1"

    if [[ "$(echo $flags | grep ^0x)" == "" ]]; then
        flags=$(printf '%x\n' "$1")
        flags="0x$flags"
    fi

    tests=(tests-mt tests-others)

    for i in $(seq 0 "$(echo ${#tests[@]}-1 | bc)"); do
        # (flag & 2^notest) >> notest # will behaviour like chmod's mode
        # if we want to run the 1st and 2nd test, our flag must be 3, and would be like
        #  (3 & 2^0) >> 0 = (0b11 & 0b01) >> 0 = 0b01 >> 0 = 0b01 = 1 == 1
        #  (3 & 2^1) >> 1 = (0b11 & 0b10) >> 1 = 0b10 >> 1 = 0b01 = 1 == 1
        if [[ "$(( ($flags & (2**$i)) >> $i ))" == "1" ]]; then
            if [ $DRYRUN = true ] ; then
                echo "${tests[$i]}"
            else
                ${tests[$i]}
            fi
        fi
    done
}

run-tests "$FLAGS"

wait

# Get hashes from all files
for TEST_ID in $(echo "10 11 100"); do
    create_integrity_report "$WORK" "${WORK}/reports/hash_values_${TEST_ID}.report" "$TEST_ID"
done

# Results
failed=$(cat "$FAILS" | wc -l)

echo "-------------------------------------"
echo "            Fails Summary            "
echo "-------------------------------------"
echo -e "status\ttest-id\texit code / desc."
cat "$FAILS"

exit "$failed"
