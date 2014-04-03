__author__ = 'pcmarks'
"""
    Provide support for accessing the GEO leveldb datastore.

"""
import leveldb
from json import JSONDecoder, JSONEncoder
import os

#############################################################################################
# Replace the following two values with the directory path of the leveldb data stores: one for
# the profile (expression) values and one for the clinical data
#
# profileOuterDirectory = '/home/pcmarks/Projects/Duarte/data/GEO'
# clinicalOuterDirectory = '/home/pcmarks/Projects/Duarte/data/GEO'
profileOuterDirectory = '/home/pcmarks/Work/MMCRI/duarte/GEO/data/database'
clinicalOuterDirectory = '/home/pcmarks/Work/MMCRI/duarte/GEO/data/database'
#############################################################################################

# Open the profile (expression) data store
profile_db = 'expression_db'
profileDatabaseDirectory = os.path.join(profileOuterDirectory, profile_db)
profile_db = leveldb.LevelDB(profileDatabaseDirectory)

# open the clinical data store
clinical_db = 'clinical_db'
clinicalDatabaseDirectory = os.path.join(clinicalOuterDirectory, clinical_db)
clinical_db = leveldb.LevelDB(clinicalDatabaseDirectory)

# Database codes that are used to create the data store keys. Parts of the keys are separated
# by "|"s
# Example Keys:
#       51              retrieves a list of cancers
#       01/ov/52        retrieves a list of profiles for ov cancer
#
SOURCE_CODE = '00'
CANCER_CODE = '01'
PROFILE_CODE = '02'
PLATFORM_CODE = '03'
SAMPLE_ID_CODE = '04'
GENE_CODE = '05'
vital_status_code = '06'
days_to_death_code = '07'
days_to_birth_code = '08'
days_to_last_followup_code = '09'
study_code = '10'
SAMPLE_ATTRIBUTES_CODE = '11'

cancers_code = '51'
profiles_code = '52'
platforms_code = '53'
sample_ids_code = '54'
genes_code = '55'
studies_code = '56'

# A list of request values for clinical data and the associated key value code.
clinical_codes = {'vital_status': vital_status_code, 'days_to_death': days_to_death_code, \
                  'days_to_birth': days_to_birth_code, 'days_to_last_followup': days_to_last_followup_code}

# A cache of gene symbols organized by profile class, e.g., Expression-Genes, Expression-miRNA, etc.
global gene_symbols_cache
gene_symbols_cache = {}

# Platforms that comprise the current cache for a profile class.
global profile_class_platforms
profile_class_platforms = {}


def switch_platform(study, profile, new_platform, old_platform):
    """

    :param study:
    :param profile:
    :param new_platform:
    :param old_platform:
    :return:
    """
    global gene_symbols_cache

    new_key = '|'.join([study, profile, new_platform])
    old_key = '|'.join([study, profile, old_platform])
    if new_platform == "none":
        if old_key in profile_class_platforms:
            del profile_class_platforms[old_key]
    elif old_platform == "none":
        profile_class_platforms[new_key] = {}
    else:
        if old_key in profile_class_platforms:
            del profile_class_platforms[old_key]
        profile_class_platforms[new_key] = {}
        # Rebuild the caches
    gene_symbols_cache = {}
    for profile_platform in profile_class_platforms:
        parts = profile_platform.split('|')
        study = parts[0]
        profile = parts[1]
        platform = parts[2]
        key = '|'.join(
            [study_code, study, PROFILE_CODE, profile, PLATFORM_CODE, platform, genes_code])
        gene_symbols = profile_db.Get(key)
        # There might be duplicate sample ids in the list - remove them
        gene_symbol_list = JSONDecoder().decode(gene_symbols)
        if profile in gene_symbols_cache:
            gene_symbols_cache[profile] = gene_symbols_cache[profile].union(gene_symbol_list)
        else:
            gene_symbols_cache[profile] = set(gene_symbol_list)
    return


def match_symbols(profile, symbols):
    """

    :param profile:
    :param symbols:
    :return:
    """
    global gene_symbols_cache

    gene_symbol_list = None
    genes = symbols.split(',')
    try:
        gene_symbol_list = gene_symbols_cache[profile]
        if genes:
            # Only grab the first gene symbol in the gene query
            gene = genes[0].upper()
            gene_symbol_list = [x for x in gene_symbol_list if gene in x]
    except KeyError:
        # No cache entry
        pass
    gene_symbols = JSONEncoder().encode(gene_symbol_list)
    return gene_symbols


def get_profile_data(study, profile, platform, genes, combined):
    """

    :param study:
    :param profile:
    :param platform:
    :param genes:
    :param combined:
    :return:
    """
    sample_attributes_list = []
    expressionValues = []
    try:
        key = '|'.join([study_code, study, PROFILE_CODE, profile, PLATFORM_CODE, platform, sample_ids_code])
        sample_ids = profile_db.Get(key)
        # There may be duplicates in the sample id list - get rid of them
        sample_id_list = JSONDecoder().decode(sample_ids)
        sample_id_list = list(set(sample_id_list))
        accepted_sample_id_list = []
        for sample_id in sample_id_list:
            try:
                attributes = profile_db.Get('|'.join( \
                    [study_code, study, PROFILE_CODE, profile, PLATFORM_CODE, platform, \
                     SAMPLE_ID_CODE, sample_id, SAMPLE_ATTRIBUTES_CODE]))
            except KeyError:
                continue

            sample_attributes_dict = JSONDecoder().decode(attributes)
            if combined and sample_attributes_dict['co_sample'] == '':
                continue
            accepted_sample_id_list.append(sample_id)
            sample_attributes_list.append(attributes)
            for gene in genes:
                try:
                    expr_value = profile_db.Get('|'.join( \
                        [study_code, study, PROFILE_CODE, profile, PLATFORM_CODE, platform, \
                         SAMPLE_ID_CODE, sample_id, GENE_CODE, gene]))
                    try:
                        val = float(expr_value)
                        expressionValues.append(val)
                    except ValueError:
                        pass
                except KeyError:
                    expressionValues.append(None)
                    #                                expr_value = None
    except KeyError:
        expressionValues = None
    result = {'values': expressionValues, 'sample_count': len(accepted_sample_id_list), \
              'sample_ids': accepted_sample_id_list, 'sample_attributes': sample_attributes_list}
    return result


def get_sample_ids(study, profile, platform):
    """

    :param study:
    :param profile:
    :param platform:
    :return:
    """
    key = '|'.join([study_code, study, PROFILE_CODE, profile, PLATFORM_CODE, platform, sample_ids_code])
    sample_ids = profile_db.Get(key)
    # There may be duplicates in the sample id list - get rid of them
    sample_id_list = JSONDecoder().decode(sample_ids)
    sample_id_list = list(set(sample_id_list))
    return sample_id_list


def get_all_gene_symbols(study, profile, platform):
    """

    :param study:
    :param profile:
    :param platform:
    :return:
    """
    key = '|'.join([study_code, study, PROFILE_CODE, profile, PLATFORM_CODE, platform, genes_code])
    genes = profile_db.Get(key)
    return JSONDecoder().decode(genes)


def get_gene_expression_value(study, profile, platform, sample_id, gene_symbol):
    """

    :param study:
    :param profile:
    :param platform:
    :param sample_id:
    :param gene_symbol:
    :return:
    """
    try:
        key = '|'.join([study_code, study, PROFILE_CODE, profile, PLATFORM_CODE, platform, \
                        SAMPLE_ID_CODE, sample_id, GENE_CODE, gene_symbol])
        expr_value = profile_db.Get(key)
    except KeyError:
        expr_value = None
    return expr_value


def get_sample_attributes(study, profile, platform, sample_id):
    """

    :param study:
    :param profile:
    :param platform:
    :param sample_id:
    :return:
    """
    attributes = None
    try:
        key = '|'.join([study_code, study, PROFILE_CODE, profile, PLATFORM_CODE, platform, \
                        SAMPLE_ID_CODE, sample_id, SAMPLE_ATTRIBUTES_CODE])
        attributes = profile_db.Get(key)
    except KeyError:
        pass

    return JSONDecoder().decode(attributes)

