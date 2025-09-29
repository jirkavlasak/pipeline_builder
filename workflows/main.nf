#!/usr/bin/env nextflow

nextflow.enable.dsl=2

process GATK HAPLOTYPECALLER {
    container 'quay.io/biocontainers/gatk4:4.4.0.0--py36hdfd78af_0'
    input:
        path input_bam
        path reference_fasta
    output:
        path "output.vcf"
    script:
    """
    gatk HaplotypeCaller -R  -I  -O {output.vcf} --stand-call-conf 30
    """
}

process MULTIQC {
    container 'quay.io/biocontainers/multiqc:1.13--pyhdfd78af_0'
    input:
        path results_dir/
    output:
        path "multiqc_report.html"
    script:
    """
    multiqc {input} -o {output_dir}
    """
}

process SAMTOOLS SORT {
    container 'quay.io/biocontainers/samtools:1.17--h00cdaf9_1'
    input:
        path input_sam
    output:
        path "sorted.bam"
    script:
    """
    samtools sort  -o {sorted.bam}
    """
}

workflow {
    data_ch = Channel.fromPath('data/*')
    gatk haplotypecaller = GATK HAPLOTYPECALLER(data_ch)
    multiqc = MULTIQC(gatk haplotypecaller)
    samtools sort = SAMTOOLS SORT(multiqc)
}