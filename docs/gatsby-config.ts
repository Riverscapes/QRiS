import { GatsbyConfig } from 'gatsby'

module.exports = {
  // You need pathPrefix if you're hosting GitHub Pages at a Project Pages or if your
  // site will live at a subdirectory like https://example.com/mypathprefix/.
  // pathPrefix: '/mypathprefix',
  flags: {
    DEV_SSR: true
  },
  siteMetadata: {
    title: `QRiS`,
    author: {
      name: `Matt Reimer`,
    },
    // Just leave this empty ('') if you don't want a help widget in the footer
    helpWidgetId: '153000000178',
    description: ``,
    siteUrl: `https://qris.riverscapes.net`,
    social: {
      twitter: `RiverscapesC`,
    },
    menuLinks: [
      {
        title: 'Getting Started',
        url: '/getting-started',
      },
      {
        title: 'About',
        url: '/about/license',
        items: [
          {
            title: 'Acknowledgements',
            url: '/about/acknowledgements',
          },
          {
            title: 'License and Source Code',
            url: '/about/license',
          },
        ],
      },
      {
        title: 'Download',
        url: '/download/install',
        items: [
          {
            title: 'Install',
            url: '/download/install',
          },
          {
            title: 'Questions, Feature Requests and Bugs',
            url: '/download/known-bugs',
          },
        ],
      },
      {
        title: 'Software Help',
        url: '/software-help',
        items: [
          {
            title: 'Toolbar',
            url: '/software-help',
          },
          {
            title: 'Project Tree',
            url: '/software-help/project-tree',
          },
          {
            title: 'Projects',
            url: '/software-help/projects',
          },
          {
            title: 'Data Capture Events',
            url: '/software-help/dce',
          },
          {
            title: 'Profiles',
            url: '/software-help/profiles',
          },
          {
            title: 'Areas of Interest',
            url: '/software-help/aoi',
          },
          {
            title: 'Surfaces',
            url: '/software-help/surfaces',
          },
          {
            title: 'Cross Sections',
            url: '/software-help/cross-sections',
          },
          {
            title: 'Sampling Frames',
            url: '/software-help/sampling-frames',
          },
          {
            title: 'Analyses',
            url: '/software-help/analyses',
          },
          {
            title: 'Zonal Statistics',
            url: '/software-help/zonal-statistics',
          },
          {
            title: 'Stream Gage Tool',
            url: '/software-help/zonal-statistics',
          },
          {
            title: 'Basemaps',
            url: '/software-help/basemaps',
          },
          {
            title: 'Context',
            url: '/software-help/context',
            items: [
              {
                title: 'Watershed Catchments',
                url: '/software-help/watershed-catchments',
              }
            ]
          }
        ],
      },
      {
        title: 'Technical Reference',
        url: '/technical-reference/database',
        items: [
          {
            title: 'Database',
            url: '/technical-reference/database',
          }
        ],
      }
    ],
  },
  plugins: [
    {
      resolve: '@riverscapes/gatsby-theme',
      options: {
        contentPath: `${__dirname}/content/page`,
        manifest: {
          name: `Riverscapes Gatsby Template Site`,
          short_name: `RiverscapesTemplate`,
          start_url: `/`,
        },
      },
    },
  ],
} as GatsbyConfig
