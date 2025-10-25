"""
Comprehensive Database Population Script
Populates database with ingredients from multiple sources: EWG, INCI Beauty, and common cosmetic ingredients
"""

import asyncio
import httpx
import logging
import json
import os
import re
import time
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urljoin
from database import SessionLocal, Ingredient, engine, Base
from ewg_scraper import EWGScraper
import random

# Configure logging with timestamps
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class ComprehensiveDatabasePopulator:
    def __init__(self):
        self.rate_limit_delay = 2  # seconds between requests
        self.batch_size = 100
        self.max_ingredients = 10000  # Increased limit for comprehensive database
        
    async def get_comprehensive_ingredient_list(self) -> List[str]:
        """Get comprehensive list of cosmetic ingredients from multiple sources"""
        all_ingredients = set()
        
        # 1. Common cosmetic ingredients (manually curated)
        common_ingredients = [
            # Water and solvents
            "water", "aqua", "glycerin", "glycerol", "propylene glycol", "butylene glycol",
            "pentylene glycol", "hexylene glycol", "caprylyl glycol", "ethylhexylglycerin",
            
            # Humectants and moisturizers
            "hyaluronic acid", "sodium hyaluronate", "squalane", "squalene", "ceramides",
            "ceramide np", "ceramide ap", "ceramide eop", "ceramide eos", "ceramide ns",
            "cholesterol", "phytosphingosine", "sphingosine", "urea", "lactic acid",
            "sodium lactate", "panthenol", "pro-vitamin b5", "allantoin", "betaine",
            
            # Oils and butters
            "jojoba oil", "argan oil", "coconut oil", "olive oil", "sunflower oil",
            "safflower oil", "grapeseed oil", "rosehip oil", "evening primrose oil",
            "borage oil", "flaxseed oil", "hemp seed oil", "avocado oil", "sweet almond oil",
            "apricot kernel oil", "macadamia oil", "shea butter", "cocoa butter",
            "mango butter", "kokum butter", "illipe butter", "murumuru butter",
            
            # Vitamins and antioxidants
            "retinol", "retinyl palmitate", "retinyl acetate", "retinyl propionate",
            "vitamin c", "ascorbic acid", "ascorbyl palmitate", "ascorbyl glucoside",
            "magnesium ascorbyl phosphate", "sodium ascorbyl phosphate", "ascorbyl tetraisopalmitate",
            "vitamin e", "tocopherol", "tocopheryl acetate", "tocopheryl linoleate",
            "vitamin a", "vitamin b3", "niacinamide", "nicotinamide", "vitamin b5",
            "pantothenic acid", "panthenol", "vitamin d", "vitamin k", "biotin",
            "folic acid", "coenzyme q10", "ubiquinone", "ferulic acid", "resveratrol",
            "polyphenols", "flavonoids", "carotenoids", "lycopene", "beta-carotene",
            
            # Acids and exfoliants
            "salicylic acid", "glycolic acid", "lactic acid", "malic acid", "tartaric acid",
            "citric acid", "mandelic acid", "azelaic acid", "kojic acid", "phytic acid",
            "alpha hydroxy acid", "beta hydroxy acid", "polyhydroxy acid", "lactobionic acid",
            
            # Peptides and proteins
            "peptides", "copper peptides", "palmitoyl pentapeptide-4", "palmitoyl tripeptide-1",
            "palmitoyl tetrapeptide-7", "palmitoyl hexapeptide-12", "acetyl hexapeptide-8",
            "collagen", "elastin", "keratin", "silk protein", "wheat protein", "soy protein",
            "rice protein", "oat protein", "quinoa protein", "hemp protein",
            
            # Preservatives
            "parabens", "methylparaben", "ethylparaben", "propylparaben", "butylparaben",
            "isobutylparaben", "phenoxyethanol", "benzyl alcohol", "dehydroacetic acid",
            "sodium dehydroacetate", "potassium sorbate", "sodium benzoate", "sorbic acid",
            "caprylyl glycol", "ethylhexylglycerin", "chlorphenesin", "imidazolidinyl urea",
            "diazolidinyl urea", "quaternium-15", "formaldehyde", "formalin",
            
            # Surfactants and cleansers
            "sodium lauryl sulfate", "sodium laureth sulfate", "ammonium lauryl sulfate",
            "cocamidopropyl betaine", "cocamidopropyl hydroxysultaine", "coco-glucoside",
            "decyl glucoside", "lauryl glucoside", "sodium cocoamphoacetate",
            "sodium lauroamphoacetate", "cocamidopropyl dimethylamine", "cocamidopropyl dimethylamine oxide",
            "sorbitan oleate", "polysorbate 20", "polysorbate 80", "polysorbate 60",
            "lecithin", "soy lecithin", "sunflower lecithin", "phospholipids",
            
            # Emulsifiers and stabilizers
            "cetearyl alcohol", "cetyl alcohol", "stearyl alcohol", "behenyl alcohol",
            "glyceryl stearate", "glyceryl distearate", "glyceryl monostearate",
            "peg-100 stearate", "peg-40 stearate", "peg-20 stearate", "stearic acid",
            "palmitic acid", "myristic acid", "lauric acid", "oleic acid", "linoleic acid",
            "arachidonic acid", "eicosapentaenoic acid", "docosahexaenoic acid",
            
            # Silicones
            "dimethicone", "cyclomethicone", "cyclopentasiloxane", "cyclohexasiloxane",
            "phenyl trimethicone", "dimethiconol", "amodimethicone", "beeswax",
            "candelilla wax", "carnauba wax", "rice bran wax", "sunflower wax",
            
            # Colorants and pigments
            "titanium dioxide", "zinc oxide", "iron oxides", "ultramarines", "chromium oxide",
            "mica", "bismuth oxychloride", "pearl powder", "aluminum powder",
            "bronze powder", "copper powder", "gold powder", "silver powder",
            
            # Sunscreens
            "avobenzone", "octinoxate", "oxybenzone", "homosalate", "octisalate",
            "octocrylene", "padimate o", "ensulizole", "sulisobenzone", "dioxybenzone",
            "meradimate", "trolamine salicylate", "cinoxate", "aminobenzoic acid",
            "ethylhexyl methoxycinnamate", "ethylhexyl salicylate", "ethylhexyl triazone",
            "diethylamino hydroxybenzoyl hexyl benzoate", "bis-ethylhexyloxyphenol methoxyphenyl triazine",
            "methylene bis-benzotriazolyl tetramethylbutylphenol", "tris-biphenyl triazine",
            
            # Fragrances and essential oils
            "parfum", "fragrance", "essential oils", "lavender oil", "rose oil",
            "jasmine oil", "ylang ylang oil", "neroli oil", "bergamot oil",
            "lemon oil", "orange oil", "grapefruit oil", "peppermint oil",
            "eucalyptus oil", "tea tree oil", "chamomile oil", "geranium oil",
            "patchouli oil", "sandalwood oil", "cedarwood oil", "frankincense oil",
            "myrrh oil", "vanilla extract", "vanilla absolute", "vanilla oleoresin",
            
            # Plant extracts
            "aloe vera", "aloe barbadensis leaf extract", "chamomile extract",
            "calendula extract", "green tea extract", "white tea extract",
            "black tea extract", "coffee extract", "cocoa extract", "cacao extract",
            "ginkgo biloba extract", "ginseng extract", "echinacea extract",
            "elderberry extract", "elderflower extract", "rosehip extract",
            "sea buckthorn extract", "pomegranate extract", "grape extract",
            "grape seed extract", "pine bark extract", "pycnogenol",
            "centella asiatica extract", "gotu kola extract", "licorice extract",
            "licorice root extract", "turmeric extract", "curcumin", "ginger extract",
            "ginger root extract", "horsetail extract", "nettle extract",
            "dandelion extract", "burdock extract", "milk thistle extract",
            "artichoke extract", "cucumber extract", "tomato extract",
            "carrot extract", "spinach extract", "kale extract", "spirulina extract",
            "chlorella extract", "kelp extract", "seaweed extract", "marine collagen",
            "marine elastin", "pearl extract", "caviar extract", "snail secretion filtrate",
            
            # Minerals and clays
            "kaolin", "bentonite", "fuller's earth", "rhassoul clay", "french green clay",
            "pink clay", "white clay", "yellow clay", "red clay", "black clay",
            "dead sea salt", "himalayan salt", "sea salt", "epsom salt",
            "magnesium chloride", "calcium carbonate", "zinc oxide", "titanium dioxide",
            "iron oxide", "chromium oxide", "ultramarine blue", "ultramarine violet",
            
            # Enzymes and probiotics
            "papain", "bromelain", "protease", "amylase", "lipase", "lactase",
            "probiotics", "lactobacillus", "bifidobacterium", "saccharomyces",
            "fermented ingredients", "kombucha", "kefir", "yogurt extract",
            
            # Preservatives and stabilizers
            "edta", "disodium edta", "trisodium edta", "tetrasodium edta",
            "bht", "bha", "tocopherol", "ascorbic acid", "citric acid",
            "sodium citrate", "potassium citrate", "calcium citrate",
            "magnesium citrate", "zinc citrate", "copper citrate",
            
            # Thickeners and gelling agents
            "xanthan gum", "guar gum", "locust bean gum", "carrageenan",
            "agar", "pectin", "algin", "sodium alginate", "calcium alginate",
            "carbomer", "acrylates copolymer", "acrylates/c10-30 alkyl acrylate crosspolymer",
            "polyacrylamide", "polyquaternium-7", "polyquaternium-10",
            "polyquaternium-11", "polyquaternium-22", "polyquaternium-39",
            "polyquaternium-47", "polyquaternium-67", "polyquaternium-68",
            "polyquaternium-69", "polyquaternium-70", "polyquaternium-71",
            "polyquaternium-72", "polyquaternium-73", "polyquaternium-74",
            "polyquaternium-75", "polyquaternium-76", "polyquaternium-77",
            "polyquaternium-78", "polyquaternium-79", "polyquaternium-80",
            "polyquaternium-81", "polyquaternium-82", "polyquaternium-83",
            "polyquaternium-84", "polyquaternium-85", "polyquaternium-86",
            "polyquaternium-87", "polyquaternium-88", "polyquaternium-89",
            "polyquaternium-90", "polyquaternium-91", "polyquaternium-92",
            "polyquaternium-93", "polyquaternium-94", "polyquaternium-95",
            "polyquaternium-96", "polyquaternium-97", "polyquaternium-98",
            "polyquaternium-99", "polyquaternium-100"
        ]
        
        all_ingredients.update(common_ingredients)
        
        # 2. Add variations and common misspellings
        variations = []
        for ingredient in common_ingredients:
            # Add common variations
            if "acid" in ingredient:
                variations.append(ingredient.replace("acid", "ate"))
                variations.append(ingredient.replace("acid", "ic acid"))
            if "oil" in ingredient:
                variations.append(ingredient.replace("oil", "oleate"))
                variations.append(ingredient.replace("oil", "olein"))
            if "extract" in ingredient:
                variations.append(ingredient.replace("extract", "essence"))
                variations.append(ingredient.replace("extract", "juice"))
        
        all_ingredients.update(variations)
        
        # 3. Add INCI names and common names
        inci_mappings = {
            "water": ["aqua", "h2o"],
            "glycerin": ["glycerol", "glycerine"],
            "hyaluronic acid": ["sodium hyaluronate", "hyaluronan"],
            "vitamin c": ["ascorbic acid", "l-ascorbic acid"],
            "vitamin e": ["tocopherol", "alpha-tocopherol"],
            "retinol": ["vitamin a", "retinyl palmitate"],
            "niacinamide": ["vitamin b3", "nicotinamide"],
            "panthenol": ["pro-vitamin b5", "pantothenic acid"],
            "squalane": ["squalene", "perhydrosqualene"],
            "dimethicone": ["polydimethylsiloxane", "pdms"],
            "cyclomethicone": ["cyclopentasiloxane", "cyclohexasiloxane"],
            "jojoba oil": ["simmondsia chinensis seed oil"],
            "argan oil": ["argania spinosa kernel oil"],
            "coconut oil": ["cocos nucifera oil"],
            "olive oil": ["olea europaea fruit oil"],
            "sunflower oil": ["helianthus annuus seed oil"],
            "rosehip oil": ["rosa canina fruit oil"],
            "evening primrose oil": ["oenothera biennis oil"],
            "borage oil": ["borago officinalis seed oil"],
            "flaxseed oil": ["linum usitatissimum seed oil"],
            "hemp seed oil": ["cannabis sativa seed oil"],
            "avocado oil": ["persea gratissima oil"],
            "sweet almond oil": ["prunus amygdalus dulcis oil"],
            "apricot kernel oil": ["prunus armeniaca kernel oil"],
            "macadamia oil": ["macadamia integrifolia seed oil"],
            "shea butter": ["butyrospermum parkii butter"],
            "cocoa butter": ["theobroma cacao seed butter"],
            "mango butter": ["mangifera indica seed butter"],
            "beeswax": ["cera alba", "cera flava"],
            "candelilla wax": ["euphorbia cerifera wax"],
            "carnauba wax": ["copernicia cerifera wax"],
            "lanolin": ["wool wax", "wool fat"],
            "squalane": ["squalene", "perhydrosqualene"],
            "ceramides": ["ceramide np", "ceramide ap", "ceramide eop"],
            "peptides": ["palmitoyl pentapeptide-4", "palmitoyl tripeptide-1"],
            "collagen": ["hydrolyzed collagen", "soluble collagen"],
            "elastin": ["hydrolyzed elastin", "soluble elastin"],
            "keratin": ["hydrolyzed keratin", "soluble keratin"],
            "silk protein": ["hydrolyzed silk", "silk amino acids"],
            "wheat protein": ["hydrolyzed wheat protein", "wheat amino acids"],
            "soy protein": ["hydrolyzed soy protein", "soy amino acids"],
            "rice protein": ["hydrolyzed rice protein", "rice amino acids"],
            "oat protein": ["hydrolyzed oat protein", "oat amino acids"],
            "quinoa protein": ["hydrolyzed quinoa protein", "quinoa amino acids"],
            "hemp protein": ["hydrolyzed hemp protein", "hemp amino acids"],
            "aloe vera": ["aloe barbadensis leaf extract", "aloe barbadensis gel"],
            "chamomile": ["chamomilla recutita extract", "matricaria chamomilla extract"],
            "calendula": ["calendula officinalis extract", "calendula officinalis flower extract"],
            "green tea": ["camellia sinensis leaf extract", "camellia sinensis extract"],
            "white tea": ["camellia sinensis leaf extract", "camellia sinensis extract"],
            "black tea": ["camellia sinensis leaf extract", "camellia sinensis extract"],
            "coffee": ["coffea arabica seed extract", "coffea arabica extract"],
            "cocoa": ["theobroma cacao extract", "theobroma cacao seed extract"],
            "cacao": ["theobroma cacao extract", "theobroma cacao seed extract"],
            "ginkgo biloba": ["ginkgo biloba leaf extract", "ginkgo biloba extract"],
            "ginseng": ["panax ginseng root extract", "panax ginseng extract"],
            "echinacea": ["echinacea purpurea extract", "echinacea purpurea root extract"],
            "elderberry": ["sambucus nigra fruit extract", "sambucus nigra extract"],
            "elderflower": ["sambucus nigra flower extract", "sambucus nigra extract"],
            "rosehip": ["rosa canina fruit extract", "rosa canina extract"],
            "sea buckthorn": ["hippophae rhamnoides fruit extract", "hippophae rhamnoides extract"],
            "pomegranate": ["punica granatum fruit extract", "punica granatum extract"],
            "grape": ["vitis vinifera fruit extract", "vitis vinifera extract"],
            "grape seed": ["vitis vinifera seed extract", "vitis vinifera seed oil"],
            "pine bark": ["pinus pinaster bark extract", "pinus pinaster extract"],
            "pycnogenol": ["pinus pinaster bark extract", "pinus pinaster extract"],
            "centella asiatica": ["centella asiatica extract", "gotu kola extract"],
            "gotu kola": ["centella asiatica extract", "gotu kola extract"],
            "licorice": ["glycyrrhiza glabra root extract", "glycyrrhiza glabra extract"],
            "licorice root": ["glycyrrhiza glabra root extract", "glycyrrhiza glabra extract"],
            "turmeric": ["curcuma longa root extract", "curcuma longa extract"],
            "curcumin": ["curcuma longa root extract", "curcuma longa extract"],
            "ginger": ["zingiber officinale root extract", "zingiber officinale extract"],
            "ginger root": ["zingiber officinale root extract", "zingiber officinale extract"],
            "horsetail": ["equisetum arvense extract", "equisetum arvense herb extract"],
            "nettle": ["urtica dioica extract", "urtica dioica leaf extract"],
            "dandelion": ["taraxacum officinale extract", "taraxacum officinale root extract"],
            "burdock": ["arctium lappa root extract", "arctium lappa extract"],
            "milk thistle": ["silybum marianum extract", "silybum marianum seed extract"],
            "artichoke": ["cynara scolymus extract", "cynara scolymus leaf extract"],
            "cucumber": ["cucumis sativus fruit extract", "cucumis sativus extract"],
            "tomato": ["solanum lycopersicum fruit extract", "solanum lycopersicum extract"],
            "carrot": ["daucus carota root extract", "daucus carota extract"],
            "spinach": ["spinacia oleracea leaf extract", "spinacia oleracea extract"],
            "kale": ["brassica oleracea acephala leaf extract", "brassica oleracea acephala extract"],
            "spirulina": ["spirulina platensis extract", "spirulina platensis powder"],
            "chlorella": ["chlorella vulgaris extract", "chlorella vulgaris powder"],
            "kelp": ["laminaria digitata extract", "laminaria digitata powder"],
            "seaweed": ["laminaria digitata extract", "laminaria digitata powder"],
            "marine collagen": ["hydrolyzed marine collagen", "soluble marine collagen"],
            "marine elastin": ["hydrolyzed marine elastin", "soluble marine elastin"],
            "pearl": ["pearl extract", "pearl powder", "pearl essence"],
            "caviar": ["caviar extract", "caviar essence"],
            "snail secretion": ["snail secretion filtrate", "snail mucin"],
            "kaolin": ["kaolin clay", "china clay"],
            "bentonite": ["bentonite clay", "montmorillonite clay"],
            "fuller's earth": ["fuller's earth clay", "attapulgite clay"],
            "rhassoul clay": ["rhassoul clay", "ghassoul clay"],
            "french green clay": ["french green clay", "illite clay"],
            "pink clay": ["pink clay", "rose clay"],
            "white clay": ["white clay", "kaolin clay"],
            "yellow clay": ["yellow clay", "illite clay"],
            "red clay": ["red clay", "illite clay"],
            "black clay": ["black clay", "illite clay"],
            "dead sea salt": ["dead sea salt", "magnesium chloride"],
            "himalayan salt": ["himalayan salt", "pink salt"],
            "sea salt": ["sea salt", "sodium chloride"],
            "epsom salt": ["epsom salt", "magnesium sulfate"],
            "magnesium chloride": ["magnesium chloride", "mgcl2"],
            "calcium carbonate": ["calcium carbonate", "caco3"],
            "zinc oxide": ["zinc oxide", "zno"],
            "titanium dioxide": ["titanium dioxide", "tio2"],
            "iron oxide": ["iron oxide", "fe2o3"],
            "chromium oxide": ["chromium oxide", "cr2o3"],
            "ultramarine blue": ["ultramarine blue", "lapis lazuli"],
            "ultramarine violet": ["ultramarine violet", "lapis lazuli"],
            "papain": ["papain enzyme", "papaya enzyme"],
            "bromelain": ["bromelain enzyme", "pineapple enzyme"],
            "protease": ["protease enzyme", "protein enzyme"],
            "amylase": ["amylase enzyme", "starch enzyme"],
            "lipase": ["lipase enzyme", "fat enzyme"],
            "lactase": ["lactase enzyme", "milk enzyme"],
            "probiotics": ["probiotic bacteria", "beneficial bacteria"],
            "lactobacillus": ["lactobacillus bacteria", "lactic acid bacteria"],
            "bifidobacterium": ["bifidobacterium bacteria", "bifidobacteria"],
            "saccharomyces": ["saccharomyces yeast", "brewer's yeast"],
            "fermented ingredients": ["fermented extracts", "fermented compounds"],
            "kombucha": ["kombucha extract", "fermented tea"],
            "kefir": ["kefir extract", "fermented milk"],
            "yogurt extract": ["yogurt extract", "fermented milk extract"],
            "edta": ["ethylenediaminetetraacetic acid", "edetic acid"],
            "disodium edta": ["disodium ethylenediaminetetraacetate", "disodium edta"],
            "trisodium edta": ["trisodium ethylenediaminetetraacetate", "trisodium edta"],
            "tetrasodium edta": ["tetrasodium ethylenediaminetetraacetate", "tetrasodium edta"],
            "bht": ["butylated hydroxytoluene", "butylhydroxytoluene"],
            "bha": ["butylated hydroxyanisole", "butylhydroxyanisole"],
            "tocopherol": ["vitamin e", "alpha-tocopherol"],
            "ascorbic acid": ["vitamin c", "l-ascorbic acid"],
            "citric acid": ["citric acid", "2-hydroxypropane-1,2,3-tricarboxylic acid"],
            "sodium citrate": ["sodium citrate", "trisodium citrate"],
            "potassium citrate": ["potassium citrate", "tripotassium citrate"],
            "calcium citrate": ["calcium citrate", "tricalcium citrate"],
            "magnesium citrate": ["magnesium citrate", "trimagnesium citrate"],
            "zinc citrate": ["zinc citrate", "zinc citrate"],
            "copper citrate": ["copper citrate", "copper citrate"],
            "xanthan gum": ["xanthan gum", "xanthomonas campestris gum"],
            "guar gum": ["guar gum", "cyamopsis tetragonoloba gum"],
            "locust bean gum": ["locust bean gum", "ceratonia siliqua gum"],
            "carrageenan": ["carrageenan", "chondrus crispus extract"],
            "agar": ["agar", "agar-agar"],
            "pectin": ["pectin", "apple pectin"],
            "algin": ["algin", "sodium alginate"],
            "sodium alginate": ["sodium alginate", "sodium salt of alginic acid"],
            "calcium alginate": ["calcium alginate", "calcium salt of alginic acid"],
            "carbomer": ["carbomer", "carbopol"],
            "acrylates copolymer": ["acrylates copolymer", "acrylic acid copolymer"],
            "acrylates/c10-30 alkyl acrylate crosspolymer": ["acrylates/c10-30 alkyl acrylate crosspolymer", "acrylic acid/c10-30 alkyl acrylate crosspolymer"],
            "polyacrylamide": ["polyacrylamide", "poly(acrylamide)"],
            "polyquaternium-7": ["polyquaternium-7", "polyquaternium 7"],
            "polyquaternium-10": ["polyquaternium-10", "polyquaternium 10"],
            "polyquaternium-11": ["polyquaternium-11", "polyquaternium 11"],
            "polyquaternium-22": ["polyquaternium-22", "polyquaternium 22"],
            "polyquaternium-39": ["polyquaternium-39", "polyquaternium 39"],
            "polyquaternium-47": ["polyquaternium-47", "polyquaternium 47"],
            "polyquaternium-67": ["polyquaternium-67", "polyquaternium 67"],
            "polyquaternium-68": ["polyquaternium-68", "polyquaternium 68"],
            "polyquaternium-69": ["polyquaternium-69", "polyquaternium 69"],
            "polyquaternium-70": ["polyquaternium-70", "polyquaternium 70"],
            "polyquaternium-71": ["polyquaternium-71", "polyquaternium 71"],
            "polyquaternium-72": ["polyquaternium-72", "polyquaternium 72"],
            "polyquaternium-73": ["polyquaternium-73", "polyquaternium 73"],
            "polyquaternium-74": ["polyquaternium-74", "polyquaternium 74"],
            "polyquaternium-75": ["polyquaternium-75", "polyquaternium 75"],
            "polyquaternium-76": ["polyquaternium-76", "polyquaternium 76"],
            "polyquaternium-77": ["polyquaternium-77", "polyquaternium 77"],
            "polyquaternium-78": ["polyquaternium-78", "polyquaternium 78"],
            "polyquaternium-79": ["polyquaternium-79", "polyquaternium 79"],
            "polyquaternium-80": ["polyquaternium-80", "polyquaternium 80"],
            "polyquaternium-81": ["polyquaternium-81", "polyquaternium 81"],
            "polyquaternium-82": ["polyquaternium-82", "polyquaternium 82"],
            "polyquaternium-83": ["polyquaternium-83", "polyquaternium 83"],
            "polyquaternium-84": ["polyquaternium-84", "polyquaternium 84"],
            "polyquaternium-85": ["polyquaternium-85", "polyquaternium 85"],
            "polyquaternium-86": ["polyquaternium-86", "polyquaternium 86"],
            "polyquaternium-87": ["polyquaternium-87", "polyquaternium 87"],
            "polyquaternium-88": ["polyquaternium-88", "polyquaternium 88"],
            "polyquaternium-89": ["polyquaternium-89", "polyquaternium 89"],
            "polyquaternium-90": ["polyquaternium-90", "polyquaternium 90"],
            "polyquaternium-91": ["polyquaternium-91", "polyquaternium 91"],
            "polyquaternium-92": ["polyquaternium-92", "polyquaternium 92"],
            "polyquaternium-93": ["polyquaternium-93", "polyquaternium 93"],
            "polyquaternium-94": ["polyquaternium-94", "polyquaternium 94"],
            "polyquaternium-95": ["polyquaternium-95", "polyquaternium 95"],
            "polyquaternium-96": ["polyquaternium-96", "polyquaternium 96"],
            "polyquaternium-97": ["polyquaternium-97", "polyquaternium 97"],
            "polyquaternium-98": ["polyquaternium-98", "polyquaternium 98"],
            "polyquaternium-99": ["polyquaternium-99", "polyquaternium 99"],
            "polyquaternium-100": ["polyquaternium-100", "polyquaternium 100"]
        }
        
        # Add INCI mappings
        for common_name, inci_names in inci_mappings.items():
            all_ingredients.add(common_name)
            all_ingredients.update(inci_names)
        
        logger.info(f"Total unique ingredients collected: {len(all_ingredients)}")
        return list(all_ingredients)[:self.max_ingredients]
    
    async def populate_database_comprehensively(self):
        """Populate database with comprehensive ingredient data"""
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        # Get comprehensive ingredient list
        ingredients_list = await self.get_comprehensive_ingredient_list()
        
        logger.info(f"Starting comprehensive database population with {len(ingredients_list)} ingredients")
        
        # Process ingredients in batches
        db = SessionLocal()
        try:
            existing_ingredients = {ing.name.lower() for ing in db.query(Ingredient).all()}
            logger.info(f"Found {len(existing_ingredients)} existing ingredients in database")
            
            processed = 0
            added = 0
            updated = 0
            
            for i in range(0, len(ingredients_list), self.batch_size):
                batch = ingredients_list[i:i + self.batch_size]
                logger.info(f"Processing batch {i//self.batch_size + 1}/{(len(ingredients_list) + self.batch_size - 1)//self.batch_size}")
                
                # Process batch concurrently
                tasks = []
                for ingredient_name in batch:
                    if ingredient_name.lower() not in existing_ingredients:
                        task = self.process_ingredient_comprehensive(ingredient_name, db)
                        tasks.append(task)
                
                if tasks:
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    for result in results:
                        if isinstance(result, Exception):
                            logger.error(f"Error processing ingredient: {result}")
                        else:
                            if result:
                                added += 1
                            processed += 1
                
                # Commit batch
                db.commit()
                logger.info(f"Batch committed. Added: {added}, Processed: {processed}")
                
                # Rate limiting between batches
                await asyncio.sleep(2)
            
            logger.info(f"Comprehensive database population complete! Added: {added}, Processed: {processed}")
            
        except Exception as e:
            logger.error(f"Error populating database: {e}")
            db.rollback()
        finally:
            db.close()
    
    async def process_ingredient_comprehensive(self, ingredient_name: str, db) -> bool:
        """Process a single ingredient with comprehensive data"""
        try:
            # Use EWG scraper to get data
            async with EWGScraper() as scraper:
                result = await scraper.get_ingredient_data(ingredient_name)
                
                if result["success"]:
                    data = result["data"]
                    
                    # Check if ingredient already exists
                    existing = db.query(Ingredient).filter(
                        Ingredient.name.ilike(ingredient_name)
                    ).first()
                    
                    if existing:
                        # Update existing ingredient
                        existing.eco_score = data.get("eco_score", existing.eco_score)
                        existing.risk_level = data.get("risk_level", existing.risk_level)
                        existing.benefits = data.get("benefits", existing.benefits)
                        existing.risks_detailed = data.get("risks_detailed", existing.risks_detailed)
                        existing.sources = data.get("sources", existing.sources)
                        logger.info(f"Updated ingredient: {ingredient_name}")
                        return True
                    else:
                        # Add new ingredient with comprehensive data
                        ingredient = Ingredient(
                            name=ingredient_name,
                            eco_score=data.get("eco_score", 50.0),
                            risk_level=data.get("risk_level", "desconocido"),
                            benefits=data.get("benefits", ""),
                            risks_detailed=data.get("risks_detailed", ""),
                            sources=data.get("sources", "EWG Skin Deep + Comprehensive Database")
                        )
                        db.add(ingredient)
                        logger.info(f"Added ingredient: {ingredient_name}")
                        return True
                else:
                    # Add ingredient with default data if EWG fails
                    existing = db.query(Ingredient).filter(
                        Ingredient.name.ilike(ingredient_name)
                    ).first()
                    
                    if not existing:
                        ingredient = Ingredient(
                            name=ingredient_name,
                            eco_score=50.0,
                            risk_level="desconocido",
                            benefits="",
                            risks_detailed="No specific data available",
                            sources="Comprehensive Database"
                        )
                        db.add(ingredient)
                        logger.info(f"Added ingredient with default data: {ingredient_name}")
                        return True
                    return False
                    
        except Exception as e:
            logger.error(f"Error processing ingredient {ingredient_name}: {e}")
            return False

async def main():
    """Main function to populate database comprehensively"""
    logger.info("Starting comprehensive database population...")
    
    populator = ComprehensiveDatabasePopulator()
    await populator.populate_database_comprehensively()
    
    logger.info("Comprehensive database population completed!")

if __name__ == "__main__":
    asyncio.run(main())