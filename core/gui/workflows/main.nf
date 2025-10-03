#!/usr/bin/env nextflow

nextflow.enable.dsl=2

process FASTQC {
    container 'quay.io/biocontainers/fastqc:0.11.9--0'
    input:
        path reads
    output:
        path '*'
    script:
    """
    fastqc --threads {--threads} ${reads} --outdir .
    """
}

process MULTIQC {
    container 'quay.io/biocontainers/multiqc:1.13--pyhdfd78af_0'
    input:
        path dummy_input
    output:
        path 'multiqc_report.html'
    script:
    """
    multiqc {results} --outdir ${task.process}
    """
}

workflow {
    FASTQC()
    MULTIQC()
}