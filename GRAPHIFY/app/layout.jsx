import './globals.css'

export const metadata = {
  title: 'GRAPHIFY - Code to Knowledge Graph',
  description: 'Visualize code as beautiful interactive knowledge graphs',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="bg-slate-950 text-slate-100">{children}</body>
    </html>
  )
}
