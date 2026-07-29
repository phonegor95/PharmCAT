#!/usr/bin/env python3
"""
Extract MT-RNR1 variants from mtdna-server-2 output and format for PharmCAT

This script parses variants.annotated.txt files from genepi/mtdna-server-2
and extracts MT-RNR1 variants that are known to PharmCAT, generating
outside call files in TSV format for use with PharmCAT's -po flag.

Author: Generated with Claude Code
Date: 2025-12-17
"""

import argparse
import csv
import logging
import os
import sys
from pathlib import Path
from typing import List, Set, Tuple, Optional


# PharmCAT-supported MT-RNR1 variants (with m. prefix)
# Based on PharmCAT/src/main/resources/org/pharmgkb/pharmcat/phenotype/MT_RNR1.json
KNOWN_MTRNR1_VARIANTS = {
    # Increased risk variants (3)
    "m.1095T>C",
    "m.1494C>T",
    "m.1555A>G",  # Most well-known aminoglycoside-associated variant

    # Normal risk variants (1)
    "m.827A>G",

    # Uncertain risk variants (20)
    "m.663A>G", "m.669T>C", "m.747A>G", "m.786G>A",
    "m.807A>C", "m.807A>G", "m.839A>G", "m.896A>G",
    "m.930G>A", "m.951G>A", "m.960C>del", "m.961T>G",
    "m.961T>del", "m.961T>del+Cn", "m.988G>A",
    "m.1189T>C", "m.1243T>C", "m.1520T>C", "m.1537C>T", "m.1556C>T",
}


class MTRNRVariantExtractor:
    """Extract and format MT-RNR1 variants from mtdna-server-2 output"""

    def __init__(self, include_unknown: bool = False, verbose: bool = False):
        """
        Initialize the extractor

        Args:
            include_unknown: If True, include variants not in PharmCAT's known list
            verbose: Enable verbose logging
        """
        self.include_unknown = include_unknown
        self.logger = self._setup_logging(verbose)

    def _setup_logging(self, verbose: bool) -> logging.Logger:
        """Set up logging configuration"""
        level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(levelname)s: %(message)s'
        )
        return logging.getLogger(__name__)

    def extract_sample_id(self, input_path: Path) -> str:
        """
        Extract sample ID from input file path

        Args:
            input_path: Path to variants.annotated.txt

        Returns:
            Sample ID string
        """
        # Try to get sample ID from parent directory name
        parent_dir = input_path.parent.name
        if parent_dir and parent_dir != 'mtdna':
            return parent_dir

        # Fallback to filename parsing
        return input_path.stem.replace('.variants.annotated', '').replace('variants.annotated', 'sample')

    def parse_variant_row(self, row: List[str], maplocus_idx: int) -> Optional[Tuple[str, str, str, str, str]]:
        """
        Parse a TSV row and extract variant information

        Args:
            row: List of column values from TSV
            maplocus_idx: Column index for Maplocus field

        Returns:
            Tuple of (sample_id, position, ref, variant, filter_status) or None if not MT-RNR1
        """
        # Column indices based on mtdna-server-2 output format
        # 0: ID, 1: Filter, 2: Pos, 3: Ref, 4: Variant, maplocus_idx: Maplocus
        if len(row) <= maplocus_idx:
            return None

        sample_id = row[0]
        filter_status = row[1]
        pos = row[2]
        ref = row[3]
        variant = row[4]
        maplocus = row[maplocus_idx]

        # Only process MT-RNR1 variants
        if maplocus != "MT-RNR1":
            return None

        return (sample_id, pos, ref, variant, filter_status)

    def format_variant_notation(self, pos: str, ref: str, variant: str) -> str:
        """
        Format variant in PharmCAT notation (with m. prefix)

        Args:
            pos: Position in mitochondrial genome
            ref: Reference allele
            variant: Variant allele

        Returns:
            Formatted variant string (e.g., "m.1555A>G")
        """
        # Handle deletions
        if not variant or variant == "-" or variant == "del":
            return f"m.{pos}{ref}>del"

        # Standard format: m.PosRef>Variant
        return f"m.{pos}{ref}>{variant}"

    def extract_variants(self, input_file: Path) -> Tuple[str, List[str], List[str]]:
        """
        Extract MT-RNR1 variants from mtdna-server-2 output file

        Args:
            input_file: Path to variants.annotated.txt

        Returns:
            Tuple of (sample_id, known_variants, unknown_variants)
        """
        known_variants = []
        unknown_variants = []
        sample_id = self.extract_sample_id(input_file)

        self.logger.info(f"Processing file: {input_file}")
        self.logger.info(f"Sample ID: {sample_id}")

        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f, delimiter='\t')

                # Read header to find Maplocus column index
                header = None
                maplocus_idx = None
                for row in reader:
                    if not row:
                        continue
                    # First non-empty row is the header
                    header = row
                    try:
                        maplocus_idx = header.index('Maplocus')
                        self.logger.debug(f"Found Maplocus column at index {maplocus_idx}")
                    except ValueError:
                        self.logger.error("Could not find 'Maplocus' column in header")
                        raise ValueError("Input file is missing 'Maplocus' column")
                    break

                if maplocus_idx is None:
                    raise ValueError("Could not parse header from input file")

                # Process data rows
                for row in reader:
                    if not row or row[0].startswith('#'):
                        continue

                    parsed = self.parse_variant_row(row, maplocus_idx)
                    if not parsed:
                        continue

                    sample_id_from_row, pos, ref, variant_allele, filter_status = parsed

                    # Only accept PASS variants by default
                    if filter_status != "PASS":
                        self.logger.debug(f"Skipping non-PASS variant at position {pos}: {filter_status}")
                        continue

                    # Format variant notation
                    variant_notation = self.format_variant_notation(pos, ref, variant_allele)

                    # Check if variant is in PharmCAT's known list
                    if variant_notation in KNOWN_MTRNR1_VARIANTS:
                        known_variants.append(variant_notation)
                        self.logger.info(f"Found known MT-RNR1 variant: {variant_notation}")
                    else:
                        unknown_variants.append(variant_notation)
                        self.logger.debug(f"Found unknown MT-RNR1 variant: {variant_notation}")

        except FileNotFoundError:
            self.logger.error(f"Input file not found: {input_file}")
            raise
        except Exception as e:
            self.logger.error(f"Error reading input file: {e}")
            raise

        return sample_id, known_variants, unknown_variants

    def write_pharmcat_output(self, output_file: Path, variants: List[str], sample_id: str):
        """
        Write PharmCAT outside call file in TSV format

        Args:
            output_file: Path to output TSV file
            variants: List of variant notations to output
            sample_id: Sample identifier
        """
        self.logger.info(f"Writing output to: {output_file}")

        try:
            with open(output_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f, delimiter='\t')

                # Write header comment
                writer.writerow(['#gene', 'diplotype', 'phenotype', 'activityScore'])

                if variants:
                    # Output each variant (monoploid gene - no slash separator)
                    for variant in variants:
                        writer.writerow(['MT-RNR1', variant, '', ''])
                        self.logger.info(f"Output: MT-RNR1\t{variant}")
                else:
                    # No known variants - output Reference
                    writer.writerow(['MT-RNR1', 'Reference', '', ''])
                    self.logger.info("Output: MT-RNR1\tReference (no known variants found)")

        except Exception as e:
            self.logger.error(f"Error writing output file: {e}")
            raise

        self.logger.info("Successfully created PharmCAT outside call file")

    def process(self, input_file: Path, output_file: Optional[Path] = None) -> Path:
        """
        Main processing pipeline

        Args:
            input_file: Path to variants.annotated.txt
            output_file: Optional path to output file (auto-generated if None)

        Returns:
            Path to created output file
        """
        # Extract variants
        sample_id, known_variants, unknown_variants = self.extract_variants(input_file)

        # Report findings
        if known_variants:
            self.logger.info(f"Found {len(known_variants)} known MT-RNR1 variant(s)")
        else:
            self.logger.info("No known MT-RNR1 variants found")

        if unknown_variants:
            if self.include_unknown:
                self.logger.warning(
                    f"Found {len(unknown_variants)} unknown MT-RNR1 variant(s): {', '.join(unknown_variants)}"
                )
                self.logger.warning("Including unknown variants in output (--include-unknown flag set)")
            else:
                self.logger.info(
                    f"Found {len(unknown_variants)} unknown MT-RNR1 variant(s) not in PharmCAT's known list"
                )
                self.logger.info("These variants will not be included in output (use --include-unknown to override)")

        # Determine which variants to output
        if self.include_unknown:
            output_variants = known_variants + unknown_variants
        else:
            output_variants = known_variants

        # Generate output filename if not provided
        if output_file is None:
            output_file = input_file.parent / f"{sample_id}.mtrnr1.tsv"

        # Write output
        self.write_pharmcat_output(output_file, output_variants, sample_id)

        return output_file


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Extract MT-RNR1 variants from mtdna-server-2 output for PharmCAT",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  %(prog)s -i variants.annotated.txt

  # Specify output file
  %(prog)s -i variants.annotated.txt -o sample.mtrnr1.tsv

  # Include unknown variants with verbose logging
  %(prog)s -i variants.annotated.txt --include-unknown --verbose

  # Use with PharmCAT
  %(prog)s -i variants.annotated.txt
  pharmcat -vcf sample.vcf -po sample.mtrnr1.tsv
        """
    )

    parser.add_argument(
        '-i', '--input',
        type=Path,
        required=True,
        help='Input variants.annotated.txt file from mtdna-server-2'
    )

    parser.add_argument(
        '-o', '--output',
        type=Path,
        help='Output TSV file path (default: <sample_id>.mtrnr1.tsv in same directory as input)'
    )

    parser.add_argument(
        '--include-unknown',
        action='store_true',
        help='Include variants not in PharmCAT\'s known MT-RNR1 list (with warning)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.0.0'
    )

    args = parser.parse_args()

    # Validate input file exists
    if not args.input.exists():
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    # Create extractor and process
    try:
        extractor = MTRNRVariantExtractor(
            include_unknown=args.include_unknown,
            verbose=args.verbose
        )
        output_file = extractor.process(args.input, args.output)
        print(f"\nSuccess! Created PharmCAT outside call file: {output_file}")
        print(f"Use with: pharmcat -vcf <your.vcf> -po {output_file}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
