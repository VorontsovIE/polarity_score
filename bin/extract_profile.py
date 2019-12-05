import sys
from pybedtools import BedTool
from dto.coding_transcript_info import CodingTranscriptInfo
from coverage_profile import transcript_coverages_from_alignment

cds_annotation_fn = sys.argv[1] # 'gencode.vM22.cds_features.tsv'
alignment_filename = sys.argv[2] # 'METTL3_ribo_Coots2017_m_r2.bam'
cds_info_by_transcript = CodingTranscriptInfo.load_transcript_cds_info(cds_annotation_fn)
alignment = BedTool(alignment_filename)
for transcript_coverage in transcript_coverages_from_alignment(alignment, sort_transcripts=False, dtype=int):
    transcript_id = transcript_coverage.transcript_id
    if transcript_id in cds_info_by_transcript:
        transcript_info = cds_info_by_transcript[transcript_id]
        cds_profile = transcript_info.cds_profile(transcript_coverage.coverage)
        print(transcript_id, ','.join(map(str, cds_profile)), sep='\t')
    else:
        print(f'Unknown transcript {transcript_id} in alignment', file=sys.stderr)