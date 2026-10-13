"""Reviewed public-source test profiles; never accept arbitrary caller commands."""
GALLERY_SHA = '3b7fe6d714cf7764e54a877c69c64eb0bdb38655'
GALLERY_FILES = ['src/components/Gallery.tsx', 'src/styles.css']
GALLERY_CRITERIA = [
    'Gallery cards are reachable with Tab and open with Enter or Space.',
    'Favorite and delete actions are visible on keyboard focus, have aria-labels, and work without opening the card.',
    'Gallery thumbnails have meaningful nonempty alt text derived from their prompts.',
    'Mouse opening, favoriting, and confirmed deletion remain functional.',
]

SLIDER_SHA = '218143b523252ee95c2368adc83fef95b324b156'
SLIDER_CURRENT_SHA = '513883a43ea33474431c933018b6267d08acb8f5'
SLIDER_FILES = ['site/index.html', 'site/assets/style.css']
SLIDER_CRITERIA = [
    'The slider is keyboard focusable with a slider role, accessible label, min/max 0/100, and accurate current value.',
    'ArrowLeft/ArrowRight adjust the split by 5 points within 0..100; Home/End select 0/100.',
    'Keyboard interaction stops automatic sweep animation and has visible focus styling.',
    'Before/after descriptions include the selected example mode and prompt and update on selection; background stays decorative.',
    'Pointer dragging and example selection still work, and reduced-motion/manual/normal video playback behavior is preserved.',
]

def profile_for(recipe):
    if recipe.editable_files == SLIDER_FILES and recipe.acceptance_criteria == SLIDER_CRITERIA:
        return 'slider-keyboard'
    if recipe.editable_files == ['site/index.html'] and len(recipe.acceptance_criteria)==3:
        return 'reduced-motion'
    if recipe.editable_files == GALLERY_FILES and recipe.acceptance_criteria == GALLERY_CRITERIA:
        return 'gallery-keyboard'
    raise ValueError('Remote recipe exceeds reviewed acceptance scope')

def validate_source(profile, repository, sha):
    if profile=='slider-keyboard':
        return repository=='davre001/kokon' and sha in {SLIDER_SHA, SLIDER_CURRENT_SHA}
    if profile=='gallery-keyboard':
        return repository=='davre001/kokon' and sha==GALLERY_SHA
    if profile=='reduced-motion':
        return repository=='gabrielelozupone/kokon' or (
            repository=='davre001/kokon' and sha=='995b078b79819c0049db3eef96fc6bd91b016b12')
    return False
