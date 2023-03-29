# Monotextor configuration file

Monotextor uses a configuration file to define the variables required by the pipeline. Depending on the options defined in this configuration file the pipeline can behave differently, running alternative tools and functionalities. The following is an exhaustive overview of all the options that can be set in the configuration file and how they affect to the pipeline.

**Suggestion**: A minimalist [configuration file sample](config/basic.yaml) is provided in this repository. You can take it as an starting point by changing all the paths to match your environment.

Current pipeline constists of the following steps:

* Crawling
* Plain text extraction
* Sharding
* Sentence splitting
* Cleaning and filtering

Following is a description of configuration related to each step, as well as basic variables.

## Data storage

There are a few variables that are mandatory for running Monotextor, independently of the task to be carried out, namely the ones related to where final & intermediate files should be stored.

```yaml
permanentDir: ~/permanent/monotextor-output
dataDir: ~/permanent/data
transientDir: ~/transient
tempDir: ~/transient
```

<!-- TODO these variables description has been documented according to their use in Bitextor. If TODO's from OUTPUT.md change, this description might change as well -->

* `permanentDir`: will contain the final results of the run, i.e. the monolingual corpus built
* `dataDir`: will contain the results of crawling (WARC files) and files generated during preprocessing (plain text extraction, sharding and sentence splitting), i.e. every step up to post-processing
* `transientDir`: will contain the results of intermediate steps related to post-processing (i.e. cleaning and filtering)
* `tempDir`: will contain temporary files that are needed by some steps and removed immediately after they are no longer required

## Workflow execution

There are some optional parameters that allow for a finer control of the execution of the pipeline, namely it is possible to configure some jobs to use more than one core; and it is possible to have a partial execution of Monotextor by specifying what step should be final.

```yaml
until: preprocess
parallelWorkers: {split: 8, monocleaner: 2}
profiling: True
```

* `until`: pipeline executes until specified step and stops. The resulting files will not necessarily be in `permanentDir`, they can also be found in `dataDir` or `transientDir` depending on the rule. Allowed values: `crawl`, `preprocess`, `shard`, `split`, `monofixer`, `monocleaner`, `filter`
* `parallelWorkers`: a dictionary specifying the number of cores that should be used for a job. Allowed values: `split`, `monofixer`, `monocleaner`, `filter`, `sents`
* `profiling`: use `/usr/bin/time` tool to obtain profiling information about each step.

## Data sources

The next set of option srefer to the source from which data will be harvested. It is possible to specify a list of websites to be crawled and/or a list of [WARC](https://iipc.github.io/warc-specifications/specifications/warc-format/warc-1.1) files that contain pre-crawled websites.
Both can be specified either via a list of source directly in the config file, or via a separated gzipped file that contains one source per line.

```yaml
hosts: ["www.elisabethtea.com","vade-antea.fr"]
hostsFile: ~/hosts.gz

warcs: ["/path/to/a.warc.gz", "/path/to/b.warc.gz"]
warcsFile: ~/warcs.gz

preverticals: ["/path/to/a.prevert.gz", "/path/to/b.prevert.gz"]
preverticalsFile: ~/preverticals.gz
```

* `hosts`: list of [hosts](https://en.wikipedia.org/wiki/URL) to be crawled; the host is the part of the URL of a website that identifies the web domain, i.e. the URL without the protocol and the path. For example, in the case of the url *<https://github.com/bitextor/monotextor>* the host would be *github.com*
* `hostsFile`: a path to a file that contains a list of hosts to be crawled; in this file each line should contain a single host, written in the format described above.
* `warcs`: specify one or multiple [WARC](https://iipc.github.io/warc-specifications/specifications/warc-format/warc-1.1) files to use; WARC files must contain individually compressed records
* `warcsFile`: a path to a file that contains a list of WARC files to be included in parallel text mining (silimar to `hosts` and `hostsFile`)
* `preverticals`: specify one or multiple prevertical files to use; prevertical files are the output of the SpiderLing crawler
* `preverticalsFile`: a path to a file that contains a list of prevertical files to be included in parallel text mining (silimar to `hosts` and `hostsFile`)

## Crawling

Three crawlers are supported by Monotextor: [Heritrix](https://github.com/internetarchive/heritrix3), `wget` tool and [linguacrawl](https://github.com/transducens/linguacrawl/). The basic options are:

```yaml
crawler: wget
crawlTimeLimit: 1h
```

* `crawler`: set which crawler is used (`heritrix`, `wget` or `linguacrawl`)
* `crawlTimeLimit`: time for which a website can be crawled; the format of this field is an integer number followed by a suffix indicating the units (accepted units are s(seconds), m(minutes), h(hours), d(days), w(weeks)), for example: `86400s`, or `1440m` or `24h`, or `1d`

### wget

`wget` is the most basic of the provided crawling tools, it will launch a crawling job for each specified host, which will be finished either when there is nothing more to download or the specified time limit has been reached. The following parameters may be configured when using this tool:

```yaml
crawlUserAgent: "Mozilla/5.0 (compatible; Monotextor/8 +https://github.com/bitextor/monotextor)"
crawlWait: 5
crawlFileTypes: ["html", "pdf"]
```

* `crawlerUserAgent`: [user agent](https://developers.whatismybrowser.com/useragents/explore/software_type_specific/crawler/) to be added to the header of the crawler when doing requests to a web server (identifies your crawler when downloading a website)
* `crawlWait`: time (in seconds) that should be waited between the retrievals; it is intended to avoid a web-site to cut the connection of the crawler due too many connections in a low interval of time
* `crawlFileTypes`: filetypes that sould be retrieved; `wget` will check the extension of the document

### Linguacrawl

Linguacrawl is a top-level domain crawler, i.e. when crawling it visits and downloads pages outside of the provided hosts.
Linguacrawl implements a scouting strategy to download the most productive content for the target languages.
The provided hosts will act a starting point for this process, the more hosts are provided the lower the chances that the crawler will run out of URLs to visit.
For this reason, the overall time taken to crawl with Linguacrawl will be significatly higher than the `crawlTimeLimit` value (as it represents the maximum time to spend in a single host).
Linguacrawl runs a single crawling job, as opposed to running a job per host, so it is recommended to use this crawler with multiple threads.

```yaml
crawlUserAgent: "Mozilla/5.0 (compatible; Monotextor/8 +https://github.com/bitextor/monotextor)"
crawlWait: 5
crawlFileTypes: ["html", "pdf"]
crawlTLD: ['es', 'fr', 'org']
crawlSizeLimit: 1024 # 1GB
crawlMaxFolderTreeDepth: 20
crawlScoutSteps: 200
crawlBlackListURL: ["wordpress", "blogspot", "facebook", "google", "wikipedia", "youtube", "perehodi", "twitter", "instagram"]
crawlPrefixFilter: ["mailto:"]
crawlerNumThreads: 1
crawlerConnectionTimeout: 10
dumpCurrentCrawl: False
resumePreviousCrawl: False

crawlCat: True
crawlCatMaxSize: 1024 # 1GB
```

* `crawlerUserAgent`: [user agent](https://developers.whatismybrowser.com/useragents/explore/software_type_specific/crawler/) to be added to the header of the crawler when doing requests to a web server (identifies your crawler when downloading a website)
* `crawlWait`: time (in seconds) that should be waited between the retrievals; it is intended to avoid a web-site to cut the connection of the crawler due to too many connections in a low interval of time
* `crawlFileTypes`: filetypes that should be retrieved; `linguacrawl` will search the provided pattern in the [Content-Type header](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Type) of the document (in this case, either the full MIME type may be specified (`text/html`,`application/pdf`), or only the subtype (`html`,`pdf`))
* `crawlTLD`: accepted [top-level domains](https://en.wikipedia.org/wiki/Top-level_domain) (TLD); the TLDs of the specified hosts, as well as the specified languages will always be added
* `crawlSizeLimit`:  maximum size limit, expressed in MB, for a single host; i.e. when this limit is reached the crawler will stop downloading pages from the host
* `crawlMaxFolderTreeDepth`: the maximum folder depth for a URL to be taken into account
* `crawlScoutSteps`: the number of documents to be downloaded from a web-site before the scouting criterion is evaluated
* `crawlBlackListURL`: a list of domains which will not be crawled, the default values are specified in the example above
* `crawlPrefixFilter`: allows to exclude documents that begin with the specified patterns, the default value is the one specified in the example above
* `crawlerNumThreads`: the number of threads to be be used by the crawler, default is 1
* `crawlerConnectionTimeout`: the connection timeout (in seconds) to a web server
* `dumpCurrentCrawl`: print progress information (WARNING: *very* verbose)
* `resumePreviousCrawl`: resume the crawling from a previous run; this option is not trivial to use since Snakemake executes the workflow based on the files which are needed, to the use this the crawling step should be re-run, which can be achieved either by removing the files so that running the crawler becomes necessary (tricky), or forcing the crawl to re-run via `--forcerun linguacrawl_download` argument provided to `monotextor` command
* `crawlCat`: allows to merge all the downloaded WARCs in just one (normally `linguacrawl` generates one warc per domain/subdomain) in order to improve the number of rules of preprocessing to run, but will result is a loss of important information like the source of the WARCs; this option should be used in conjunction with `crawlCatMaxSize` to avoid generating WARCs that are extremely large
* `crawlCatMaxSize`: intead of generating a single WARC, generate multiple WARCs of the specified size, expressed in MB

If Linguacrawl is used, a YAML file is created on the fly in order to use it as configuration file, and you can check this file out to be sure that is configured as you want. There are multiple options which are provided with a default value if none was set, so might be interesting to visualize the generated YAML configuration file if you want a concrete behaviour or something is not working as you expected. Those default values are set because are mandatory for Linguacrawl. Other than the parameters explained above, default behaviour which should be taken into account is:

* A maximum of 3 attempts will be made in order to download a resource.
* The number of minimum languages in a site will be 2, and in the case of not satisfy this condition, the site will be discarted
* The mandatory lang to be found in a site will be determined by `lang1` or `lang2` if not defined. A minimum of 10% of content has to be present in the mandatory language in order to not discard a resource
* The accepted TLDs will be those specified in `lang1`, `lang2`, `langs` and `crawlTLD`
* WARNING: if you use linguacrawl in a cluster, it is highly recommended to use `crawlCat` and `crawlCatMaxSize` in order to balance the work (it is not usual to use a crawler in a cluster)

### Heritrix

Finally, to use **Heritrix**, these parameters must be set:

```yaml
crawler: heritrix
heritrixPath: /home/user/heritrix-3.4.0-20190418
heritrixUrl: "https://localhost:8443"
heritrixUser: "admin:admin"
```

* `heritrixPath` is the installation folder of heritirx
* `heritrixUrl` is the URL where heritrix service is running, `https://localhost:8443` by default
* `heritrixUser` provides the necessary credentials to access heritrix service in the format of `login:password` (`admin:admin`) by default

Heritrix crawler will check if there is a checkpoint in its 'jobs' folder and resume from the latest. If crawl takes longer than the crawl time limit, it will automatically create a checkpoint for a future incremental crawl.

## Preprocessing and sharding

After crawling, the downloaded webs are processed to extract clean text, detect language, etc.

After plain text extracion, the extracted data is sharded via [giashard](https://github.com/paracrawl/giashard) in order to create balanced jobs.
Crawled websites and WARCs are distributed in shards for a more balanced processing, where each shard contains one or more complete domain(s).
Shards in turn are split into batches of specified size to keep memory consumption in check.

The following set of option define how that process is carried out.

```yaml
# preprocessing
preprocessor: warc2text
langs: [en, es, fr]

## with warc2preprocess only
parser: "bs4"
ftfy: False
cleanHTML: False
langID: cld2

## remove boilerplate, only warc2preprocess in WARC processing and prevertical2text in prevertical files
boilerplateCleaning: true

## identify paragraphs
paragraphIdentification: true

# sharding
shards: 8 # 2^8 shards
batches: 1024 # batches of up to 1024MB
```

* `preprocessor`: this options allows to select one of two text extraction tools, `warc2text` (default) or `warc2preprocess`. `warc2text` is faster but less flexible (less options) than `warc2preprocess`. There is another preprocessor, but cannot be set, and that is `prevertical2text`. This preprocessor will be used automatically when you have prevertical files, which is the format of the SpiderLing crawler. The reason why cannot be set is because is not a generic preprocessor, but specific for SpiderLing files.
* `langs`: list of languages that will be processed

Options specific to `warc2preprocess`:

* `langID`: the model that should be used for language identification, [`cld2`](https://github.com/CLD2Owners/cld2) (default) or [`cld3`](https://github.com/google/cld3); `cld2` is faster, but `cld3` can be more accurate for certain languages
* `ftfy`: ftfy is a tool that solves encoding errors (disabled by default)
* `cleanHTML`: attempt to remove some parts of HTML that don't contain text (such as CSS, embedded scripts or special tags) before running ftfy, which is a quite slow, in order to improve overall speed; this has an unwanted side effect of removing too much content if the HTML document is malformed (disabled by default)
* `html5lib`: extra parsing with [`html5lib`](https://pypi.org/project/html5lib/), which is slow but the cleanest option and parses the HTML the same way as the modern browsers, which is interesting for broken HTMLs (disabled by default)
* `boilerplateCleaning`: enable [boilerpipe](https://boilerpipe-web.appspot.com/) to remove boilerplates from HTML documents (disabled by default)
* `parser`: select HTML parsing library for text extraction; options are: [`bs4`](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) (default), [`modest`](https://github.com/rushter/selectolax), `lxml` (uses `html5lib`) or `simple` (very basic HTML tokenizer)
* `PDFextract`: use [PDFExtraxt](https://github.com/bitextor/python-pdfextract) instead of poppler `pdf2html` converter
* `PDFextract_configfile`: set a path for a PDFExtract config file, specially for language models for a better sentence splitting (see [more info](https://github.com/bitextor/pdf-extract/#pdfextractjson))
* `PDFextract_sentence_join_path`: set a path for sentence-join.py script, otherwise, the one included with monotextor will be used
* `PDFextract_kenlm_path`: set path for kenlm binaries

Boilerplate:

* `boilerplateCleaning`: if `preprocessor: warc2preprocess`, enables [boilerpipe](https://boilerpipe-web.appspot.com/) to remove boilerplates from HTML documents. If you have provided `preverticals` files, it will discard those entries detected as boilerplate by `prevertical2text` automatically. `warc2text` does not support this option. It is disabled by default

Paragraph identification:

* `paragraphIdentification`: if this option is enabled, the selected `preprocessor` will generate information which will identify the paragraphs. This information will be used to link every sentence to the position which it took in the original paragraph. If `skipSentenceSplitting: true`, the paragraph information will be just the position of the paragraph in the document

Sharding options:

* `shards`: set number of shards, where a value of 'n' will result in 2^n shards, default is 8 (2^8 shards); `shards: 0` will force all domains to be in the same shard
* `batches`: batch size in MB, default is 1024; large batches will increase memory consumption, but will reduce time overhead

## Sentence splitting

By default a Python wrapper of [Loomchild Segment](https://github.com/bitextor/loomchild-segment-py) will be used for sentence splitting.

<!-- TODO different TODO's added to the Snakefile because the options are not in the file args.py
By default a Python port of [Moses `split-sentences.perl`](https://pypi.org/project/sentence-splitter/) will be used for sentence splitting. This is recommened even without language support, since it is possible to provide custom non-breaking prefixes. External sentence splitter can by used via `sentence-splitters` parameter (less efficient).

Custom sentence splitters must read plain text documents from standard input and write one sentence per line to standard output.

```yaml
sentenceSplitters: {
  'fr': '/home/user/monotextor/preprocess/moses/ems/support/split-sentences.perl -q -b -l fr',
  'default': '/home/user/monotextor/monotextor/example/nltk-sent-tokeniser.py english'
}

customNBPs: {
  'fr': '/home/user/monotextor/myfrenchnbp.txt'
}
```

* `sentenceSplitters`: provide custom scripts for sentence segmentation per language, script specified under `default` will be applied to all lanuages
* `customNBPs`: provide a set of files with custom Non-Breaking Prefixes for the default sentence-splitter; see [already existing files](https://github.com/berkmancenter/mediacloud-sentence-splitter/tree/develop/sentence_splitter/non_breaking_prefixes) for examples

-->

## Monolingual data filtering

Monolingual data filtering is carried out with [Monocleaner](https://github.com/bitextor/monocleaner); this tool uses a pre-trained regression model to filter out segments with a low confidence score.

A number of pre-trained models for Monocleaner are available [here](https://github.com/bitextor/monocleaner-data/releases/latest). They are ready to be downloaded and decompressed.

The options required to make it work are:

```yaml
monocleaner: True
monocleanerModels: {"fr": "/home/user/monocleaner-model/fr"}
monocleanerThreshold: 0.5
```

* `monocleaner`: use Monocleaner to filter out pairs of segments
* `monocleanerModel`: path to the YAML configuration file of a pre-trained model
* `monocleanerThreshold`: threshold to filter low-confidence segment pairs, accepts values in [0,1] range; default is 0.0 (no filtering). It is recommended to set it to values in [0.5,0.7]


## Post-processing

Some other options can be configured to specify the output format of the monolingual corpus:

```yaml
monofixer: True
monofixerTitles: False
sensitiveData: False

deferred: False
```

* `monofixer`: use [Monofixer](https://github.com/bitextor/bifixer) to fix parallel sentences and tag near-duplicates for removal <!-- When using `bifixer: True` it is possible to specify additional arguments using `bifixerOptions` variable. More information about these arguments in [Monofixer](https://github.com/bitextor/bifixer) repository. -->
* `monofixerTitles`: apply monofixer to document titles extracted from preverticals.
* `sensitiveData`: detect sensitive data (IPs, emails and phone numbers) for paragraphs. Adds an extra column saying "yes" or "no".
* `deferred`: if this option is set, segment contents are deferred to the original location given a Murmurhash2 64bit checksum
