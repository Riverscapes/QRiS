import { themes as prismThemes } from 'prism-react-renderer'
import type { Config } from '@docusaurus/types'
import type * as Preset from '@docusaurus/preset-classic'

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

const config: Config = {
  title: 'QRiS', // Site title displayed in the browser tab
  tagline: 'Riverscapes Studio for QGIS', // Short description shown in meta tags
  favicon: 'qris-icon.png', // Path to site favicon

  future: {
    v4: true, // Enables compatibility with upcoming Docusaurus v4 features
  },

  url: 'https://qris.riverscapes.net', // The base URL of your site (no trailing slash)
  baseUrl: '/', // The sub-path where your site is served (used in GitHub Pages)

  // GitHub pages deployment config
  organizationName: 'Riverscapes', // GitHub org/user name
  projectName: 'qris-docs', // GitHub repo name

  onBrokenLinks: 'throw', // Throw an error on broken links
  onBrokenMarkdownLinks: 'warn', // Warn instead of throwing for broken markdown links

  i18n: {
    defaultLocale: 'en', // Default language
    locales: ['en'], // Supported languages
  },

  themes: ['@riverscapes/docusaurus-theme'], // Shared custom theme used across sites

  presets: [
    [
      'classic', // Docusaurus classic preset for docs/blog
      {
        gtag: {
          trackingID: 'G-WSJ6478P6E',
          anonymizeIP: true,
        },
        docs: {
          sidebarPath: './sidebars.ts', // Path to sidebar config
          routeBasePath: '/', // Serve docs at site root
          editUrl: 'https://github.com/Riverscapes/QRiS/tree/docs/docs/', // "Edit this page" link
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    image: 'images/logo.png', // Social sharing image

    algolia: {
      // The application ID provided by Algolia
      appId: '4TGS8ZPIMY',

      // Public API key: it is safe to commit it
      apiKey: 'd084a7919fe7b5940d7125f14221eaca',

      indexName: 'qris.riverscapes.net',

      // Optional: see doc section below
      contextualSearch: true,

      // Optional: Specify domains where the navigation should occur through window.location instead on history.push. Useful when our Algolia config crawls multiple documentation sites and we want to navigate with window.location.href to them.
      // externalUrlRegex: "external\\.com|domain\\.com",

      // Optional: Replace parts of the item URLs from Algolia. Useful when using the same search index for multiple deployments using a different baseUrl. You can use regexp or string in the `from` param. For example: localhost:3000 vs myCompany.com/docs
      // replaceSearchResultPathname: {
      //   from: "/docs/", // or as RegExp: /\/docs\//
      //   to: "/",
      // },

      // Optional: Algolia search parameters
      // searchParameters: {},

      // Optional: path for search page that enabled by default (`false` to disable it)
      // searchPagePath: "search",

      // Optional: whether the insights feature is enabled or not on Docsearch (`false` by default)
      // insights: false,

      //... other Algolia params
    },

    navbar: {
      title: 'Riverscapes Studio (QRiS)',
      logo: {
        alt: 'QRiS Logo',
        src: 'images/logo.png',
      },
      items: [
        //   {
        //     label: "About",
        //     position: "left",
        //     items: [
        //       { to: "/About/acknowledgements", label: "Acknowledgements" },
        //       { to: "/About/license", label: "License and Source Code" },
        //     ],
        //   },
        //   {
        //     label: "Download",
        //     position: "left",
        //     items: [
        //       { to: "/Download/install", label: "Install" },
        //       {
        //         to: "/Download/known-bugs",
        //         label: "Questions, Feature Requests and Bugs",
        //       },
        //     ],
        //   },
        //   {
        //     label: "Software Help",
        //     position: "left",
        //     items: [
        //       { to: "/software-help/analyses", label: "Analyses" },
        //       { to: "/software-help/aoi", label: "Areas of Interest" },
        //       { to: "/software-help/basemaps", label: "Basemaps" },
        //       {
        //         to: "/software-help/batch-attribute-editor",
        //         label: "Batch Attribute Editor",
        //       },
        //       { to: "/software-help/context/", label: "Context" },
        //       { to: "/software-help/cross-sections", label: "Cross Sections" },
        //       { to: "/software-help/dce", label: "Data Capture Events" },
        //       { to: "/software-help/metrics", label: "Metrics" },
        //       { to: "/software-help/profiles", label: "Profiles" },
        //       { to: "/software-help/project-tree", label: "Project Tree" },
        //       { to: "/software-help/projects", label: "Projects" },
        //       { to: "/software-help/sample-frames", label: "Sample Frames" },
        //       { to: "/software-help/surfaces", label: "Surfaces" },
        //       {
        //         to: "/software-help/zonal-statistics",
        //         label: "Zonal Statistics",
        //       },
        //       //     {
        //       //       label: 'Context',
        //       //       items: [
        //       //         { to: '/software-help/context', label: 'Context' },
        //       //         { to: '/software-help/stream-gage-tool', label: 'Stream Gage Tool' },
        //       //         { to: '/software-help/watershed-catchments', label: 'Watershed Catchments' },
        //       //       ],
        //       //     },
        //     ],
        //   },
        //   {
        //     label: "Tutorials",
        //     position: "left",
        //     items: [
        //       { to: "/tutorials/conceptual-overview", label: "Conceptual Overview" },
        //       { to: "/tutorials/starting-a-project", label: "Starting a Project" },
        //       { to: "/tutorials/create-a-design", label: "Create a Design" },
        //       { to: "/tutorials/create-as-build", label: "Create an As-Built" },
        //       { to: "/tutorials/digitizing", label: "Digitizing in QGIS" },
        //       { to: "/tutorials/sharing-projects", label: "Sharing Projects" },
        //     ],
        //   },
        //   {
        //     label: "Technical Reference",
        //     position: "left",
        //     items: [
        //       { to: "/technical-reference/database", label: "Database" },
        //       {
        //         to: "/technical-reference/managing_metrics",
        //         label: "Managing Metrics",
        //       },
        //       {
        //         to: "/technical-reference/metric_calculations",
        //         label: "Metric Calculations",
        //       },
        //     ],
        //   },

        {
          href: 'https://github.com/Riverscapes/QRiS', // External GitHub link
          label: 'GitHub',
          position: 'right',
        },
      ],
    },

    footer: {
      links: [
        {
          // Note that this NEEDS to match what's in the default template or we get another column
          title: 'User Resources',
          items: [
            {
              label: 'Join this User Community',
              href: 'https://www.riverscapes.net/topics/33160/feed',
            },
            {
              label: 'Search the Data Exchange',
              href: 'https://data.riverscapes.net/s?type=Project&projectTypeId=riverscapesstudio&view=map',
            },
            {
              label: 'Developers & Code Repository',
              href: 'https://github.com/Riverscapes/QRiS',
            },
            {
              label: 'Knowledge Base',
              href: 'https://riverscapes.freshdesk.com/a/solutions/categories/153000297758/folders/153000763613?view=all',
            },
          ],
        },
      ],
    },

    prism: {
      theme: prismThemes.github, // Code block theme for light mode
      darkTheme: prismThemes.dracula, // Code block theme for dark mode
    },
  } satisfies Preset.ThemeConfig,
}

export default config
