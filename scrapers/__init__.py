from .ebay import EbayScraper
from .ebay_uk import EbayUKScraper
from .poshmark import PoshmarkScraper
from .vinted import VintedScraper
from .vinted_uk import VintedUKScraper

ALL_SCRAPERS = [EbayScraper, EbayUKScraper, VintedScraper, VintedUKScraper, PoshmarkScraper]
