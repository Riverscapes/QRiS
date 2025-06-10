import { themes as prismThemes } from 'prism-react-renderer'
import type { Config } from '@docusaurus/types'
import type * as Preset from '@docusaurus/preset-classic'

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

const config: Config = {
  title: 'Riverscapes Studio', // Site title displayed in the browser tab
  tagline: 'Riverscapes Developer Resources', // Short description shown in meta tags
  favicon: 'img/favicon.ico', // Path to site favicon

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
        docs: {
          sidebarPath: './sidebars.ts', // Path to sidebar config
          routeBasePath: '/', // Serve docs at site root
          editUrl: 'https://github.com/Riverscapes/QRiS/tree/docs/', // "Edit this page" link
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    image: 'images/logo.png', // Social sharing image

    navbar: {
      title: 'Riverscapes Studio',
      logo: {
        alt: 'QRiS Logo',
        src: 'images/logo.png',
      },
      items: [
        { to: '/getting-started', label: 'Getting Started', position: 'left' },
        {
          label: 'About',
          position: 'left',
          items: [
            { to: '/About/acknowledgements', label: 'Acknowledgements' },
            { to: '/About/license', label: 'License and Source Code' },
          ],
        },
        {
          label: 'Download',
          position: 'left',
          items: [
            { to: '/Download/install', label: 'Install' },
            { to: '/Download/known-bugs', label: 'Questions, Feature Requests and Bugs' },
          ],
        },
        {
          label: 'Software Help',
          position: 'left',
          items: [
            { to: '/software-help/analyses', label: 'Analyses' },
            { to: '/software-help/aoi', label: 'Areas of Interest' },
            { to: '/software-help/basemaps', label: 'Basemaps' },
            { to: '/software-help/batch-attribute-editor', label: 'Batch Attribute Editor' },
            { to: '/software-help/context', label: 'Context'},
            { to: '/software-help/cross-sections', label: 'Cross Sections' },
            { to: '/software-help/dce', label: 'Data Capture Events' },
            { to: '/software-help/metrics', label: 'Metrics' },
            { to: '/software-help/profiles', label: 'Profiles' },
            { to: '/software-help/project-tree', label: 'Project Tree' },
            { to: '/software-help/projects', label: 'Projects' },
            { to: '/software-help/sample-frames', label: 'Sample Frames' },
            { to: '/software-help/surfaces', label: 'Surfaces' },
            { to: '/software-help/zonal-statistics', label: 'Zonal Statistics' },
        //     {
        //       label: 'Context',
        //       items: [
        //         { to: '/software-help/context', label: 'Context' },
        //         { to: '/software-help/stream-gage-tool', label: 'Stream Gage Tool' },
        //         { to: '/software-help/watershed-catchments', label: 'Watershed Catchments' },
        //       ],
        //     },
          ],
        },
        {
          label: 'Technical Reference',
          position: 'left',
          items: [
            { to: '/technical-reference/database', label: 'Database' },
            { to: '/technical-reference/managing_metrics', label: 'Managing Metrics' },
            { to: '/technical-reference/metric_calculations', label: 'Metric Calculations' },
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


// menuLinks: [
//   {
//     title: 'Getting Started',
//     url: '/getting-started',
//   },
//   {
//     title: 'About',
//     url: '/About/license',
//     items: [
//       {
//         title: 'Acknowledgements',
//         url: '/About/acknowledgements',
//       },
//       {
//         title: 'License and Source Code',
//         url: '/About/license',
//       },
//     ],
//   },
//   {
//     title: 'Download',
//     url: '/Download/install',
//     items: [
//       {
//         title: 'Install',
//         url: '/Download/install',
//       },
//       {
//         title: 'Questions, Feature Requests and Bugs',
//         url: '/Download/known-bugs',
//       },
//     ],
//   },
//   {
//     title: 'Software Help',
//     url: '/software-help',
//     items: [
//       {
//         title: 'Toolbar',
//         url: '/software-help',
//       },
//       {
//         title: 'Project Tree',
//         url: '/software-help/project-tree',
//       },
//       {
//         title: 'Projects',
//         url: '/software-help/projects',
//       },
//       {
//         title: 'Data Capture Events',
//         url: '/software-help/dce',
//       },
//       {
//         title: 'Profiles',
//         url: '/software-help/profiles',
//       },
//       {
//         title: 'Areas of Interest',
//         url: '/software-help/aoi',
//       },
//       {
//         title: 'Surfaces',
//         url: '/software-help/surfaces',
//       },
//       {
//         title: 'Cross Sections',
//         url: '/software-help/cross-sections',
//       },
//       {
//         title: 'Sample Frames',
//         url: '/software-help/sample-frames',
//       },
//       {
//         title: 'Analyses',
//         url: '/software-help/analyses',
//       },
//       {
//         title: 'Metrics',
//         url: '/software-help/metrics',
//       },
//       {
//         title: 'Analyses',
//         url: '/software-help/analyses',
//       },
//       {
//         title: 'Zonal Statistics',
//         url: '/software-help/zonal-statistics',
//       },
//       {
//         title: 'Basemaps',
//         url: '/software-help/basemaps',
//       },
//       {
//         title: 'Context',
//         url: '/software-help/context',
//         items: [
//           {
//             title: 'Stream Gage Tool',
//             url: '/software-help/stream-gage-tool',
//           },
//           {
//             title: 'Watershed Catchments',
//             url: '/software-help/watershed-catchments',
//           }
//         ]
//       }
//     ],
//   },
//   {
//     title: 'Technical Reference',
//     url: '/technical-reference/database',
//     items: [
//       {
//         title: 'Database',
//         url: '/technical-reference/database',
//       },
//       {
//         title: 'Managing Metrics',
//         url: '/technical-reference/managing_metrics',
//       },
//       {
//         title: 'Metric Calculations',
//         url: '/technical-reference/metric_calculations',
//       }
//     ],
//   }
// ],