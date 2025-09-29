#!/usr/bin/env nextflow

nextflow.enable.dsl=2

process FASTQC {
    container 'quay.io/biocontainers/fastqc:0.11.9--0'
    input:
        path '/home/vlasakj/data/sample.fastq.zip'
    output:
        path 'fastqc_report.html'
    script:
    """
    fastqc --threads 2 /home/vlasakj/data/sample.fastq.zip --outdir '/home/vlasakj/output/'
    """
}

workflow {
    fastqc = FASTQC(path='/home/vlasakj/data/sample.fastq.zip')
}
