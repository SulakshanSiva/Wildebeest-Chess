import React from 'react'

const Menu = () => {
  return (
    <main className='menu min-h-screen overflow-hidden bg-[#10271d] text-white'>
      <div className='menu__board' aria-hidden='true' />
      <div className='menu__overlay' aria-hidden='true' />

      <section className='menu__content px-6 text-center'>
        <p className='mb-4 text-xs font-semibold uppercase tracking-[0.45em] text-[#d9bd78] sm:text-sm'>
          A custom game of strategy
        </p>
        <h1 className='font-cinzel text-5xl font-bold leading-tight text-[#fff8e7] drop-shadow-[0_4px_0_rgba(31,18,8,0.35)] sm:text-7xl md:text-8xl'>
          Wildebeest Chess
        </h1>
        <div className='mt-10 flex flex-col items-center gap-4'>
          <button
            type='button'
            onClick={() => undefined}
            className='menu__play-button w-40 rounded-full border border-[#f2d894] bg-[#d9bd78] px-10 py-3 font-cinzel text-sm font-bold uppercase tracking-[0.2em] text-[#243b2b] transition hover:bg-[#f2d894] focus:outline-none focus:ring-2 focus:ring-[#fff8e7] focus:ring-offset-2 focus:ring-offset-[#243b2b]'
          >
            Play
          </button>
          <button
            type='button'
            onClick={() => undefined}
            className='menu__play-button w-40 rounded-full border border-[#f2d894] bg-[#d9bd78] px-10 py-3 font-cinzel text-sm font-bold uppercase tracking-[0.2em] text-[#243b2b] transition hover:bg-[#f2d894] focus:outline-none focus:ring-2 focus:ring-[#fff8e7] focus:ring-offset-2 focus:ring-offset-[#243b2b]'
          >
            Rules
          </button>
        </div>
      </section>

      <footer className='menu__credits'>
        <a
          href='https://github.com/SulakshanSiva/Wildebeest-Chess'
          target='_blank'
          rel='noreferrer'
          className='text-xs tracking-[0.16em] text-[#fff8e7]/75 transition hover:text-[#fff8e7] focus:outline-none focus:ring-2 focus:ring-[#f2d894] focus:ring-offset-2 focus:ring-offset-[#243b2b]'
        >
          View source on GitHub
        </a>
      </footer>
    </main>
  )
}

export default Menu
