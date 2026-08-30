import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { LandingPage } from './LandingPage';

describe('LandingPage Component', () => {
  it('renders landing hero text correctly', () => {
    render(
      <BrowserRouter>
        <LandingPage />
      </BrowserRouter>
    );

    expect(screen.getByText(/Healthcare intelligence,/i)).toBeInTheDocument();
    expect(screen.getByText(/made visible\./i)).toBeInTheDocument();
    expect(screen.getByText(/Explore CAREFlow Platform/i)).toBeInTheDocument();
  });

  it('renders section narrative headings', () => {
    render(
      <BrowserRouter>
        <LandingPage />
      </BrowserRouter>
    );

    expect(screen.getByText(/Healthcare systems are/i)).toBeInTheDocument();
    expect(screen.getByText(/Intelligence Architecture/i)).toBeInTheDocument();
  });
});
