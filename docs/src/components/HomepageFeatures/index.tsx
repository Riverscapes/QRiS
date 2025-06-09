import React from 'react'
import styles from './styles.module.css'
// import useBaseUrl from '@docusaurus/useBaseUrl'

export default function HomepageFeatures() {
  return (
    <div className={styles.container}>
      <section title="Home" className={styles.intro}>
        <p>
QGIS Riverscapes Studio or QRiS is a plugin that helps you digitize your riverscape data. 
It provides a flexible, extensible structure for your data, together with consistent symbology 
to streamline your data capture, monitoring and analysis.
        </p>

        <p>
QRiS is a plugin to the free, open-source <a href="https://qgis.org/en/site/">QGIS</a> desktop GIS software. 
QRiS is targeted at anyone interested in understanding and analyzing their riverscape - including:  
practitioners, managers, analysts, researchers and students with some familiarity with GIS. 
It helps users with analysis, monitoring, assessment of riverscapes as well as preparation of the 
design and as-builts of low-tech process-based restoration designs.
        </p>
        <p>
QRiS is currently in beta and available as an experimental plugin in the QGIS plugin repository. 
We are actively developing the tool and welcome feedback and contributions. 
Please get in touch if you would like to get involved.
        </p>
      </section>

      <Section title="Sub-pages of this site:">
        <CardGrid>
          <ResourceCard
            title="Standards & Compliance"
            description="Learn about riverscapes standards and how to make your tools and data compliant."
            link="standards"
          />
          <ResourceCard
            title="Riverscapes API"
            description="Learn how to use the Riverscapes API to access data."
            link="dev-tools/api"
          />
          <ResourceCard
            title="Documentation"
            description="Resources to build Riverscapes documentation and websites."
            link="documentation/documentation-websites"
          />
        </CardGrid>
      </Section>

      <Section title="Other Riverscapes Sites">
        <CardGrid>
          <ResourceCard
            title="Riverscapes Consortium"
            description="The Riverscapes Consortium main site."
            link="https://riverscapes.net"
          />
          <ResourceCard
            title="Our Tools"
            description="Learn about each of our Riverscapes compliant tools."
            link="https://tools.riverscapes.net/"
          />
          <ResourceCard
            title="Data Exchange"
            description="Discover and download Riverscapes compliant data."
            link="https://data.riverscapes.net/"
          />
        </CardGrid>
      </Section>


    </div>
  )
}

function Section({ title, children }) {
  return (
    <div className={styles.section}>
      <h2>{title}</h2>
      {children}
    </div>
  )
}

function CardGrid({ children }) {
  return <div className={styles.grid}>{children}</div>
}

function ResourceCard({ title, description, link }) {
  return (
    <a href={link} className={styles.card}>
      {/* <img src={useBaseUrl('/img/card-image.jpg')} alt={title} className={styles.cardImage} /> */}
      <div className={styles.cardContent}>
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
    </a>
  )
}
