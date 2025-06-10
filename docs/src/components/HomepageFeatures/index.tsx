import React from 'react'
import styles from './styles.module.css'
// import useBaseUrl from '@docusaurus/useBaseUrl'

export default function HomepageFeatures() {
  return (
    <div className={styles.container}>
      <section title="Home" className={styles.intro}>

<p>QGIS Riverscapes Studio, or QRiS, is a plugin that helps you digitize your riverscape data. 
It provides a flexible, extensible structure for your spatial layers, together with consistent symbology 
to streamline your data capture, monitoring and analysis.</p>

<p>QRiS is a plugin to the free, open-source <a href="https://qgis.org/en/site/">QGIS</a> desktop GIS software. 
QRiS is targeted at anyone interested in understanding and analyzing their riverscape, including:  
practitioners, managers, analysts, researchers and students with some familiarity with GIS. 
It helps users with analysis, monitoring, assessment of riverscapes as well as preparation of the 
design and as-builts of low-tech process-based restoration designs.</p>
      </section>
      <Section title="">
        <CardGrid>
          <ResourceCard
            title="Download QRiS"
            description="Learn how to find, install the QRiS plugin for QGIS, as well as check for updates."
            link="Download/install"
          />
          <ResourceCard
            title="Getting Started"
            description="Discover the basic workflow of using QRiS. Create a QRiS project, add data, and start digitizing."
            link="getting-started"
          />
          <ResourceCard
            title="Software Help"
            description="Comprehensive how-to guides for using every QRiS feature."
            link="software-help"
          />
        </CardGrid>
      </Section>

      <Section title="Other Riverscapes Sites">
        <CardGrid>
          <ResourceCard
            title="Riverscapes Consortium"
            description="The main site for the Riverscapes Consortium."
            link="https://riverscapes.net"
          />
          <ResourceCard
            title="Riverscapes Data Exchange"
            description="A public platform for discovering, sharing, and downloading Riverscapes compliant data."
            link="https://data.riverscapes.net/"
          />
          <ResourceCard
            title="QRiS User Community"
            description="A public forum where you can ask questions, share experiences, and connect with other QRiS users."
            link="https://www.riverscapes.net/topics/33160/feed"
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
