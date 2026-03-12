export default function Home() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-8">
      <main className="flex max-w-2xl flex-col items-center gap-8 text-center">
        <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
          Cold Start AI
        </h1>
        <p className="text-lg text-gray-600 dark:text-gray-400">
          Your complete go-to-market system — positioning, ICP, channels,
          messaging, playbooks, sequences, and metrics — generated in minutes.
        </p>
        <div className="flex gap-4">
          <a
            href="#"
            className="rounded-lg bg-black px-6 py-3 text-sm font-medium text-white hover:bg-gray-800 dark:bg-white dark:text-black dark:hover:bg-gray-200"
          >
            Get Started
          </a>
        </div>
      </main>
    </div>
  );
}
