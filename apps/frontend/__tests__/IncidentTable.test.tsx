import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { IncidentTable } from '@/components/IncidentTable'

const mockIncidents = [
  {
    incident_id: 'INC-001',
    id: 'INC-001',
    title: 'Stuck Order',
    description: 'Order pending too long',
    severity: 'high',
    status: 'open',
    type: 'stuck_order',
    desk: 'FX',
    created_at: new Date().toISOString(),
  },
  {
    incident_id: 'INC-002',
    id: 'INC-002',
    title: 'Volume Spike',
    description: 'Unusual volume',
    severity: 'medium',
    status: 'investigating',
    type: 'spike',
    desk: 'Equities',
    created_at: new Date(Date.now() - 3600000).toISOString(),
  },
]

describe('IncidentTable', () => {
  it('renders no incidents message when empty', () => {
    render(<IncidentTable incidents={[]} />)
    expect(screen.getByText('No incidents found')).toBeInTheDocument()
  })

  it('renders incident rows', () => {
    render(<IncidentTable incidents={mockIncidents} />)
    expect(screen.getByText('Stuck Order')).toBeInTheDocument()
    expect(screen.getByText('Volume Spike')).toBeInTheDocument()
    expect(screen.getByText('high')).toBeInTheDocument()
    expect(screen.getByText('medium')).toBeInTheDocument()
    expect(screen.getByText('open')).toBeInTheDocument()
    expect(screen.getByText('investigating')).toBeInTheDocument()
  })

  it('calls onSelect when row is clicked', () => {
    const onSelect = jest.fn()
    render(<IncidentTable incidents={mockIncidents} onSelect={onSelect} />)
    fireEvent.click(screen.getByText('Stuck Order').closest('tr')!)
    expect(onSelect).toHaveBeenCalledWith(mockIncidents[0])
  })

  it('supports bulk selection and resolve', () => {
    const onBulkResolve = jest.fn()
    render(<IncidentTable incidents={mockIncidents} onBulkResolve={onBulkResolve} />)
    const checkboxes = screen.getAllByRole('checkbox')
    fireEvent.click(checkboxes[1])
    expect(screen.getByText(/1 selected/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /Resolve/i }))
    expect(onBulkResolve).toHaveBeenCalled()
    expect(onBulkResolve.mock.calls[0][0]).toContain('INC-001')
  })

  it('sorts by column when header is clicked', () => {
    render(<IncidentTable incidents={mockIncidents} />)
    fireEvent.click(screen.getByText('Severity'))
    fireEvent.click(screen.getByText('Time'))
  })
})
