"""Reviewed public-source test profiles; never accept arbitrary caller commands."""
GALLERY_SHA = '3b7fe6d714cf7764e54a877c69c64eb0bdb38655'
GALLERY_FILES = ['src/components/Gallery.tsx', 'src/styles.css']
GALLERY_CRITERIA = [
    'Gallery cards are reachable with Tab and open with Enter or Space.',
    'Favorite and delete actions are visible on keyboard focus, have aria-labels, and work without opening the card.',
    'Gallery thumbnails have meaningful nonempty alt text derived from their prompts.',
    'Mouse opening, favoriting, and confirmed deletion remain functional.',
]

def profile_for(recipe):
    if recipe.editable_files == ['site/index.html'] and len(recipe.acceptance_criteria)==3:
        return 'reduced-motion'
    if recipe.editable_files == GALLERY_FILES and recipe.acceptance_criteria == GALLERY_CRITERIA:
        return 'gallery-keyboard'
    raise ValueError('Remote recipe exceeds reviewed acceptance scope')

def validate_source(profile, repository, sha):
    if profile=='gallery-keyboard':
        return repository=='davre001/kokon' and sha==GALLERY_SHA
    if profile=='reduced-motion':
        return repository=='gabrielelozupone/kokon' or (
            repository=='davre001/kokon' and sha=='995b078b79819c0049db3eef96fc6bd91b016b12')
    return False
