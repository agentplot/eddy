// The site, built by Astro with Starlight and published to GitHub Pages at
// https://agentplot.github.io/eddy by .github/workflows/pages.yml. The
// diagrams are drawn by docs/diagrams/diagrams.py into src/generated/
// before every build and dev (scripts/diagrams.mjs).
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import starlightLinksValidator from 'starlight-links-validator';

export default defineConfig({
  site: 'https://agentplot.github.io',
  base: '/eddy',
  integrations: [
    starlight({
      title: 'eddy',
      description: 'eddy lists recorded meetings across services, with no model running, and keeps each transcript whole for a session to read later.',
      logo: {
        light: './src/assets/mark-light.svg',
        dark: './src/assets/mark-dark.svg',
        alt: 'eddy',
      },
      favicon: '/favicon.svg',
      // The family's bar and footer from @agentplot/site-theme, which find
      // eddy by the title above; the start page's hero, with the animated
      // diagram, where every other page keeps Starlight's.
      components: {
        Header: '@agentplot/site-theme/starlight/Header.astro',
        Footer: '@agentplot/site-theme/starlight/Footer.astro',
        Hero: './src/components/Hero.astro',
      },
      // The family's type, colours and eddy's accent from the theme, then
      // what is eddy's own: the diagrams' palette.
      customCss: ['@agentplot/site-theme/starlight.css', './src/styles/brand.css'],
      social: [{ icon: 'github', label: 'GitHub', href: 'https://github.com/agentplot/eddy' }],
      editLink: {
        baseUrl: 'https://github.com/agentplot/eddy/edit/main/site/',
      },
      plugins: [starlightLinksValidator()],
      sidebar: [
        { label: 'Start', link: '/' },
        { label: 'How it works', link: '/how-it-works/' },
        { label: 'How it fits', link: '/how-it-fits/' },
        { label: 'Design', link: '/design/' },
        { label: 'Roadmap', link: '/roadmap/' },
      ],
    }),
  ],
});
