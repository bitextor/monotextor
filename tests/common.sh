#!/bin/bash

get_nolines()
{
    zcat $1 2> /dev/null | wc -l
}

download_file()
{
    local path=$1
    local remote=$2

    if [ ! -f "${path}" ]; then
        wget -q "${remote}" -O "${path}"
    fi
}

download_monocleaner_model()
{
    local base="https://github.com/bitextor/monocleaner-data/releases/latest/download"
    local langs=$1
    local output=$2
    if [ ! -f "${output}/${langs}.tgz" ]; then
        wget -q "${base}/${langs}.tgz" -P "${output}"
        tar xzf "${output}/${langs}.tgz" -C "${output}"
    fi
}

# Run tests
annotate_and_echo_info()
{
    local test_id=$1
    local status=$2
    local nolines=$3
    local error_file="$FAILS"

    if [[ "$status" == "0" ]] && [[ "$nolines" != "0" ]]; then
        echo "Ok ${test_id} (nolines: ${nolines})"
    else if [[ "$status" != "0" ]]; then
        echo "Failed ${test_id} (status: ${status})"
        echo "fail ${test_id} ${status}" >> "$error_file"
    else if [[ "$nolines" == "0" ]]; then
        echo "Failed ${test_id} (nolines: ${nolines})"
        echo "fail ${test_id} '0 no. lines'" >> "$error_file"
    fi
    fi
    fi
}

init_test()
{
    # Export these variables to the global scope
    TEST_ID="$1"
    TRANSIENT_DIR="${WORK}/transient/${TEST_ID}"

    mkdir -p "${TRANSIENT_DIR}"
    pushd "${TRANSIENT_DIR}" > /dev/null
}

finish_test()
{
    local status="$?"
    local langs="$1"
    local common_suffix="$2"

    for lang in $(echo "$langs"); do
      annotate_and_echo_info "${TEST_ID}.${lang}" "$status" "$(get_nolines ${WORK}/permanent/$TEST_ID/${lang}.${common_suffix})"
    done
}

get_hash()
{
    if [ ! -f "$1" ]; then
        echo "file_not_found"
    else
        local CAT=$([[ "$1" == *.gz ]] && echo "zcat" || echo "cat")

        $CAT "$1" | md5sum | awk '{print $1}'
    fi
}

test_finished_successfully()
{
    local report_file="$1"

    if [[ ! -f "$report_file" ]]; then
        echo "false"
        return
    fi

    local rule_all=$(cat "$report_file" | grep "^localrule all:$" | wc -l)
    local steps=$(cat "$report_file" | grep -E "^[0-9]+ of [0-9]+ steps \(100%\) done$" | wc -l)

    if [[ "$rule_all" != "0" ]] && [[ "$steps" != "0" ]]; then
        echo "true"
    else
        echo "false"
    fi
}

create_integrity_report()
{
    local WORK="$1"
    local INTEGRITY_REPORT="$2"
    local TEST_ID="$3"
    local DIR="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
    local TEST_OK=$(test_finished_successfully "${WORK}/reports/${TEST_ID}.report")

    if [[ "$TEST_OK" == "false" ]]; then
        return
    fi

    if [[ -f "$INTEGRITY_REPORT" ]]; then
        local random=$(echo "$(echo $RANDOM)+$(date)" | md5sum | head -c 20)
        local new_name=$(echo "${INTEGRITY_REPORT}.${random}.report")

        >&2 echo "Integrity file already exists: moving '${INTEGRITY_REPORT}' to '${new_name}'"

        mv "$INTEGRITY_REPORT" "$new_name"
    fi

    for f in $(echo "${WORK}/permanent/${TEST_ID} ${WORK}/transient/${TEST_ID} ${WORK}/data/${TEST_ID}"); do
        if [[ ! -d "$f" ]]; then
            >&2 echo "Directory '$f' does not exist"
            continue
        fi

        find "$f" -type f \
            | grep -E -v "/[.]snakemake(/|$)" \
            | xargs -I{} bash -c 'source "'${DIR}'/common.sh"; h=$(get_hash "{}"); echo "{}: ${h}"' >> "${INTEGRITY_REPORT}"
    done
}
