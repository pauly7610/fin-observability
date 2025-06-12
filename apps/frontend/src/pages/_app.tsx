import type { AppProps } from 'next/app';
import Head from 'next/head';
import '../styles/globals.css';

export default function App({ Component, pageProps }: AppProps) {
  return (
    <>
      <Head>
        <title>Fin Observability</title>
        <meta name="description" content="Financial Observability Dashboard" />
        <meta name="theme-color" content="#1f2937" />
      </Head>
      <div className="min-h-screen bg-base-300" data-theme="dark">
        <Component {...pageProps} />
      </div>
    </>
  );
}