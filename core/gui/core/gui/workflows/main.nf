#!/usr/bin/env nextflow

nextflow.enable.dsl=2

process FASTQC {
    container 'quay.io/biocontainers/fastqc:0.11.9--0'
    input:
    path reads
    output:
    path '*_fastqc.zip', emit: zip
    path '*_fastqc.html', emit: html
    script:
    """
    fastqc --threads 2 ${reads} --outdir .
    """
}

process MULTIQC {
    container 'quay.io/biocontainers/multiqc:1.13--pyhdfd78af_0'
    input:
    output:
    path 'multiqc_report.html'
    script:
    """
    multiqc . --outdir ${task.process}
    """
}

workflow {
    FASTQC_IN = Channel.fromPath('/home/vlasakj/R22THP_D1_Colibri_S4_R1_001.fastq.gz')
    params.outdir = '/home/vlasakj/work'
    FASTQC(FASTQC_IN)
    MULTIQC()
}