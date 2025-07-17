# GitHub Pages Documentation

This directory contains the GitHub Pages configuration for the Video Processing Tool documentation website.

## Setup

The site is automatically deployed using GitHub Actions when changes are pushed to the main branch.

### Files

- `index.md` - Main documentation page (mirrors the repository README)
- `_config.yml` - Jekyll configuration for GitHub Pages
- `../.github/workflows/pages.yml` - GitHub Actions workflow for deployment

### Local Development

To run the site locally:

1. Install Jekyll and dependencies:
   ```bash
   gem install jekyll bundler
   bundle install
   ```

2. Serve the site:
   ```bash
   bundle exec jekyll serve --source docs
   ```

3. Open http://localhost:4000 in your browser

### Theme

The site uses the default GitHub Pages theme (minima) with:
- Responsive design
- Syntax highlighting for code blocks
- SEO optimization
- Automatic sitemap generation

### Customization

To customize the appearance:
1. Edit `_config.yml` for site-wide settings
2. Add custom CSS in `assets/css/style.scss`
3. Override theme layouts in `_layouts/`
4. Add custom includes in `_includes/`

The site will be available at: https://nipunbatra.github.io/video-toolkit