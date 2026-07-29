__author__ = 'BinglanLi'

from pathlib import Path


# partial credit to Heroico (GitHub User Name) and https://github.com/hakyimlab/MetaXcan


class ReportableException(Exception):
    """Simple exception with message(s)"""
    def __init__(self, msg: str):
        self.msg: str = msg

    def __str__(self):
        return self.msg


class InappropriateVCFSuffix(ReportableException):
    """Inappropriate VCF suffix (not ending with .vcf.gz)"""
    def __init__(self, msg: Path | str):
        super().__init__('Inappropriate VCF suffix (not ending with .vcf, .vcf.gz, .vcf.bgz, .bcf, or .bcf.bgzf): %s' % str(msg))


class InvalidURL(ReportableException):
    """Inappropriate URL. No downloadable content was found."""
    def __init__(self, url: str):
        super().__init__('Invalid URL: %s' % url)
