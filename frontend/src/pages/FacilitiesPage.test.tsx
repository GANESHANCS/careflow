import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { FacilitiesPage } from './FacilitiesPage';
import { api } from '../api/client';

vi.mock('../api/client', () => ({
  api: {
    getFacilities: vi.fn(),
  },
}));

describe('FacilitiesPage Component', () => {
  const mockFacilitiesList = [
    {
      id: 'fac-101',
      facility_code: 'DH101',
      facility_name: 'District Hospital Mysuru',
      facility_type: 'District Hospital',
      state: 'Karnataka',
      district: 'Mysuru',
      sub_district: 'Mysuru Urban',
    },
    {
      id: 'fac-102',
      facility_code: 'CHC102',
      facility_name: 'Community Health Centre Hunsur',
      facility_type: 'CHC',
      state: 'Karnataka',
      district: 'Mysuru',
      sub_district: 'Hunsur',
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders facilities directory table correctly when API succeeds', async () => {
    vi.mocked(api.getFacilities).mockResolvedValue({
      items: mockFacilitiesList,
      total: 2,
      skip: 0,
      limit: 100,
    });

    render(
      <BrowserRouter>
        <FacilitiesPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Facility Intelligence Directory/i)).toBeInTheDocument();
      expect(screen.getAllByText(/District Hospital Mysuru/i)[0]).toBeInTheDocument();
      expect(screen.getAllByText(/Community Health Centre Hunsur/i)[0]).toBeInTheDocument();
    });
  });

  it('filters facilities list when typing in search input', async () => {
    vi.mocked(api.getFacilities).mockResolvedValue({
      items: mockFacilitiesList,
      total: 2,
      skip: 0,
      limit: 100,
    });

    render(
      <BrowserRouter>
        <FacilitiesPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getAllByText(/District Hospital Mysuru/i)[0]).toBeInTheDocument();
    });

    const searchInput = screen.getByLabelText(/Search facilities by name, district, or code/i);
    fireEvent.change(searchInput, { target: { value: 'Hunsur' } });

    expect(screen.getAllByText(/Community Health Centre Hunsur/i)[0]).toBeInTheDocument();
    expect(screen.queryByText(/District Hospital Mysuru/i)).not.toBeInTheDocument();
  });

  it('renders empty state when search returns zero results', async () => {
    vi.mocked(api.getFacilities).mockResolvedValue({
      items: mockFacilitiesList,
      total: 2,
      skip: 0,
      limit: 100,
    });

    render(
      <BrowserRouter>
        <FacilitiesPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getAllByText(/District Hospital Mysuru/i)[0]).toBeInTheDocument();
    });

    const searchInput = screen.getByLabelText(/Search facilities by name, district, or code/i);
    fireEvent.change(searchInput, { target: { value: 'NonexistentHospital123' } });

    expect(screen.getByText(/NO MATCHING FACILITIES FOUND/i)).toBeInTheDocument();
  });

  it('renders error state and handles try again button', async () => {
    vi.mocked(api.getFacilities).mockRejectedValue(new Error('Network Connection Error'));

    render(
      <BrowserRouter>
        <FacilitiesPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Network Connection Error/i)).toBeInTheDocument();
    });

    const tryAgainBtn = screen.getByRole('button', { name: /try again/i });
    expect(tryAgainBtn).toBeInTheDocument();
  });
});
