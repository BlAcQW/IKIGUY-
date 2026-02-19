import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'KasaAI Developer Documentation',
  tagline: 'Build powerful voice AI and automation workflows',
  favicon: 'img/favicon.ico',

  // Future flags
  future: {
    v4: true,
  },

  // Production URL
  url: 'https://docs.ailabsafrica.com',
  baseUrl: '/',

  // GitHub org/repo
  organizationName: 'ailabsafrica',
  projectName: 'kasaai',

  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          routeBasePath: '/', // Serve docs at root
          editUrl: 'https://github.com/alfredanyan/kasaai-v2/tree/main/apps/docs/',
        },
        blog: false, // Blog disabled for now
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    // Social card for sharing
    image: 'img/kasaai-social-card.jpg',

    // Color mode configuration
    colorMode: {
      defaultMode: 'light',
      disableSwitch: false,
      respectPrefersColorScheme: true,
    },

    // Announcement bar (can be used for updates)
    announcementBar: {
      id: 'v1_launch',
      content: '🎉 Welcome to KasaAI v1 API! <a target="_blank" rel="noopener noreferrer" href="/getting-started/quickstart">Get started in 5 minutes</a>',
      backgroundColor: '#6366f1',
      textColor: '#ffffff',
      isCloseable: true,
    },

    // Navbar configuration
    navbar: {
      title: 'KasaAI',
      logo: {
        alt: 'KasaAI Logo',
        src: 'img/logo.png',
        srcDark: 'img/logo-dark.png',
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'gettingStartedSidebar',
          position: 'left',
          label: 'Getting Started',
        },
        {
          type: 'docSidebar',
          sidebarId: 'guidesSidebar',
          position: 'left',
          label: 'Guides',
        },
        {
          type: 'docSidebar',
          sidebarId: 'apiReferenceSidebar',
          position: 'left',
          label: 'API Reference',
        },
        {
          type: 'docSidebar',
          sidebarId: 'useCasesSidebar',
          position: 'left',
          label: 'Use Cases',
        },
        {
          type: 'docSidebar',
          sidebarId: 'internalSidebar',
          position: 'left',
          label: 'Internal',
        },
        {
          type: 'docsVersionDropdown',
          position: 'right',
          dropdownActiveClassDisabled: true,
        },
        {
          href: 'https://developer.ailabsafrica.com',
          label: 'Developer Console',
          position: 'right',
        },
        {
          href: 'https://github.com/alfredanyan/kasaai-v2',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },

    // Footer configuration
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Documentation',
          items: [
            {
              label: 'Getting Started',
              to: '/getting-started/introduction',
            },
            {
              label: 'API Reference',
              to: '/api-reference/overview',
            },
            {
              label: 'Use Cases',
              to: '/use-cases/customer-support-bot',
            },
            {
              label: 'Changelog',
              to: '/changelog',
            },
          ],
        },
        {
          title: 'Resources',
          items: [
            {
              label: 'Developer Console',
              href: 'https://developer.ailabsafrica.com',
            },
            {
              label: 'Status Page',
              href: 'https://status.ailabsafrica.com',
            },
            {
              label: 'Support Portal',
              href: 'https://support.ailabsafrica.com',
            },
            {
              label: 'Postman Collection',
              href: 'https://postman.com/ailabsafrica/kasaai',
            },
          ],
        },
        {
          title: 'Community',
          items: [
            {
              label: 'GitHub',
              href: 'https://github.com/alfredanyan/kasaai-v2',
            },
            {
              label: 'Discord',
              href: 'https://discord.gg/kasaai',
            },
            {
              label: 'Stack Overflow',
              href: 'https://stackoverflow.com/questions/tagged/kasaai',
            },
            {
              label: 'Twitter',
              href: 'https://twitter.com/kasaai',
            },
          ],
        },
        {
          title: 'Legal',
          items: [
            {
              label: 'Terms of Service',
              href: 'https://ailabsafrica.com/terms',
            },
            {
              label: 'Privacy Policy',
              href: 'https://ailabsafrica.com/privacy',
            },
            {
              label: 'Security',
              href: 'https://ailabsafrica.com/security',
            },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} AI Labs Africa. Built with ❤️ for developers.`,
    },

    // Syntax highlighting configuration
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['bash', 'python', 'javascript', 'typescript', 'json', 'php', 'java', 'go', 'rust'],
    },

    // Algolia search (add your config when ready)
    // algolia: {
    //   appId: 'YOUR_APP_ID',
    //   apiKey: 'YOUR_SEARCH_API_KEY',
    //   indexName: 'kasaai',
    //   contextualSearch: true,
    // },
  } satisfies Preset.ThemeConfig,

  // Plugins
  plugins: [
    // Add plugins here as needed
  ],
};

export default config;
