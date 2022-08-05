# Monotextor output

Monotextor generates the final monolingual corpora in multiple formats. These files will be placed in `permanentDir` folder and will have the following naming convention: `{lang}.{prefix}.gz`, where `{prefix}` corresponds to a descriptor of the corresponding format and/or granularity of the data.

## Default

The file that will be always generated (regardless of configuration) is `{lang}.raw.gz`. This file comes in Moses format, i.e. **tab-separated** columns.

<!-- TODO currently, the output files are being deduplicated, but this might change. If changes, update this documentation -->

* `{lang}.raw.gz`: monolingual corpus that contains every sentence or paragraph. The file has **has deduplication** and the content is **not filtered**.

    This file contains columns added by different optional modules/features: **paragraph identification**, **deferred**, **Monofixer** and **Monocleaner**. In case some of these are not enabled, the corresponding columns will be omitted. The possible fields that may appear in this file are (in this order):

    1. `url text` - default columns
        * `url` is the source document of the text
        * `text` is the content in `{lang}`
    2. `paragraph_id` - paragraph identification data
        * initial position of the sentence in the paragraph, and initial position of the paragraph in the document
    3. `deferred_hash` - deferred hash of the text
        * may be used to reconstruct the original corpus using [Deferred crawling reconstructor](https://github.com/bitextor/deferred-crawling)
    4. `monofixer_hash monofixer_score` - Monofixer output
        * `monofixer_hash` tags duplicate or near-duplicate text
        * `monofixer_score` rates quality of duplicate or near-duplicate text
    5. `monocleaner_lang_id monocleaner_score` - Monocleaner classifer output
        * `monocleaner_lang_id` is the lang which Monocleaner detects
        * `monocleaner_score` is the quality metric of Monocleaner for the text

    This file comes accompanied by the corresponding statistics file `{lang}.stats.raw`, which provides information the size of the corpus in MB and in number of tokens.

<!-- TODO update if necessary when above TODO had been resolved -->

* `{lang}.sent.gz`: monolingual corpus with a granularity of sentences which is generated if `skipSentenceSplitting: false` or not provided. The content of the file is the same that `{lang}.raw.gz`.

* `{lang}.raw.paragraphs.gz`: monolingual corpus with a granularity of paragraphs which is generated if `skipSentenceSplitting: true`. The content of the file is the same that `{lang}.raw.gz`.
