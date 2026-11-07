import { Hero } from '../components/home/Hero'
import { HowItWorks } from '../components/home/HowItWorks'
import { IntegrationsTeaser } from '../components/home/IntegrationsTeaser'
import { ProductPreview } from '../components/home/ProductPreview'

export default function Home() {
  return (
    <>
      <Hero />
      <ProductPreview />
      <HowItWorks />
      <IntegrationsTeaser />
    </>
  )
}
