# Accessibility Requirements (WCAG 2.2)

WCAG 2.2 became an ISO standard in 2025, superseding WCAG 2.1. The contrast ratio requirements are unchanged from 2.1, but 2.2 adds new success criteria around focus appearance and consistent help.

## Caption Requirements
- Complete sentence introducing the diagram (before the visual)
- Figure caption with end punctuation
- Self-contained (PM can understand without surrounding text)
- Conversational language, avoid jargon
- Label units and scales where applicable

## Alt Text Requirements
- Short description (<155 characters)
- Identifies what diagram shows
- Avoid "Image of" or "Diagram of"
- Consider surrounding context

## Long Description (for complex diagrams)
- Detailed textual representation
- Explain all essential information conveyed
- Describe relationships, flows, or structures shown

## Visual Design
- 4.5:1 minimum contrast ratio for text (7:1 ideal for AAA compliance)
- 3:1 minimum contrast ratio for graphical objects and UI components
- Don't rely on color alone - use shapes, patterns, labels
- High contrast, 12pt+ text
- Consistent icon set and naming scheme
- Use semantic color conventions (see `color-palette.md`)

## Accessibility Compliance

**All color combinations in the recommended palette meet WCAG 2.2 standards:**
- Text on fill backgrounds: 7:1+ contrast ratio (AAA)
- Stroke on fill: 3:1+ contrast ratio (AA)
- Verified with WebAIM Contrast Checker: https://webaim.org/resources/contrastchecker/

**Colorblind Considerations:**
- Avoid red/green combinations together
- Blue, orange, purple, and green families are distinguishable for most colorblind types
- Always combine color with text labels (never rely on color alone)

## Verification Tools

- **WebAIM Contrast Checker**: https://webaim.org/resources/contrastchecker/ - Standard WCAG 2.2 contrast verification
- **Polypane**: Checks both WCAG 2 and APCA contrast, with built-in accessibility inspector
- **Colour Contrast Analyser (CCA)**: Desktop tool from TPGi for checking contrast against WCAG 2.2
- **Coblis Colorblind Simulator**: https://www.color-blindness.com/coblis-color-blindness-simulator/ - Upload images to see through colorblind vision
- **DaltonLens**: More scientifically rigorous colorblind simulation based on peer-reviewed models (recommended for precise verification)

## Future Direction: APCA

The Advanced Perceptual Contrast Algorithm (APCA) is under development as part of WCAG 3.0 (Working Draft as of Sep 2025). APCA provides more perceptually accurate contrast calculations than the current WCAG 2.x luminance formula. However, WCAG 3.0 is not expected to become a standard before 2028. For now, continue using WCAG 2.2 contrast ratios as the authoritative standard.
