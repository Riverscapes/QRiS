import { GatsbyConfig } from 'gatsby'

module.exports = {
  // You need pathPrefix if you're hosting GitHub Pages at a Project Pages or if your
  // site will live at a subdirectory like https://example.com/mypathprefix/.
  // pathPrefix: '/mypathprefix',
  pathPrefix: '/riverscapes-template',
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
        url: '/software-help/index',
        items: [
          {
            title: 'Toolbar',
            url: '/software-help/index',
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
          start_url: `/riverscapes-template`,
        },
      },
    },
  ],
} as GatsbyConfig
