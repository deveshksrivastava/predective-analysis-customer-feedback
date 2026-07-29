import { useEffect, useState } from 'react'
import { ChevronDown } from 'lucide-react'
import SourceTypeDropdown from './SourceTypeDropdown.tsx'

const descriptions: Record<string, string> = {
  'upload-dap':
    'This option is designed for datasets that need to be manually uploaded and managed within the platform, such as lookup tables, reference data, or other baseline data. The onboarding process captures the metadata and governance details required to register, catalogue, and manage the dataset.',
}

type BusinessFunction = {
  id: string
  name: string
  ownerEmail: string
  memberEmails: [string, string, string]
}

// Stand-in for the real business-function service. Same async shape as the
// eventual fetch() call, so swapping it out later is a body change only.
const businessFunctions: BusinessFunction[] = [
  {
    id: 'rasp',
    name: 'RASP',
    ownerEmail: 'test1@gmail.com',
    memberEmails: ['test2@gmail.com', 'test3@gmail.com', 'test4@gmail.com'],
  },
  {
    id: 'finance',
    name: 'Finance',
    ownerEmail: 'finance.owner@company.com',
    memberEmails: [
      'finance.member1@company.com',
      'finance.member2@company.com',
      'finance.member3@company.com',
    ],
  },
  {
    id: 'risk',
    name: 'Risk & Compliance',
    ownerEmail: 'risk.owner@company.com',
    memberEmails: [
      'risk.member1@company.com',
      'risk.member2@company.com',
      'risk.member3@company.com',
    ],
  },
  {
    id: 'supply-chain',
    name: 'Supply Chain',
    ownerEmail: 'supply.owner@company.com',
    memberEmails: [
      'supply.member1@company.com',
      'supply.member2@company.com',
      'supply.member3@company.com',
    ],
  },
]

async function fetchBusinessFunctions(): Promise<BusinessFunction[]> {
  await new Promise((resolve) => setTimeout(resolve, 300))
  return businessFunctions
}

function IntakeForm({
  sourceType,
  onSourceTypeChange,
}: {
  sourceType: string | null
  onSourceTypeChange: (key: string) => void
}) {
  const selected = sourceType
  const description = selected ? descriptions[selected] : undefined

  const [businessFunction, setBusinessFunction] = useState('')
  const [ownerEmail, setOwnerEmail] = useState('')
  const [memberEmail1, setMemberEmail1] = useState('')
  const [memberEmail2, setMemberEmail2] = useState('')
  const [memberEmail3, setMemberEmail3] = useState('')
  const [options, setOptions] = useState<BusinessFunction[]>([])

  useEffect(() => {
    let active = true
    fetchBusinessFunctions()
      .then((result) => {
        if (active) setOptions(result)
      })
      .catch((error) => console.error('Could not load business functions', error))
    return () => {
      active = false
    }
  }, [])

  function handleBusinessFunctionChange(value: string) {
    setBusinessFunction(value)
    const match = options.find((option) => option.id === value)
    setOwnerEmail(match?.ownerEmail ?? '')
    setMemberEmail1(match?.memberEmails[0] ?? '')
    setMemberEmail2(match?.memberEmails[1] ?? '')
    setMemberEmail3(match?.memberEmails[2] ?? '')
  }

  return (
    <div className="w-full pl-14 pr-8 py-6">
      <h1 className="text-lg font-semibold text-gray-900 border-b-2 border-gray-300 pb-0.5 mb-6">
        Intake Options
      </h1>

      <label className="flex items-center gap-1 text-sm font-semibold text-gray-700 mb-2">
        <span className="text-rose-500">*</span> Intake Source Type
      </label>
      <SourceTypeDropdown value={selected} onChange={onSourceTypeChange} />

      {description && (
        <p className="ml-4 pr-4 text-xs text-gray-500 mb-8">{description}</p>
      )}

      {selected === 'upload-dap' && (
        <>
          <h2 className="text-xl font-semibold text-gray-900 border-b-2 border-gray-300 pb-0.5 mb-6">
            Business Function
          </h2>
          <label className="ml-4 block text-sm font-semibold text-gray-700 mb-1">
            Business Function Name
          </label>
          <div className="relative ml-4 w-[calc(95%-1rem)] mb-8">
            <select
              value={businessFunction}
              onChange={(event) => handleBusinessFunctionChange(event.target.value)}
              className="w-full appearance-none bg-white border border-gray-300 rounded px-3 py-2 text-xs text-black"
            >
              <option value="" disabled>
                Create / Select Business Function
              </option>
              {options.map((option) => (
                <option key={option.id} value={option.id}>
                  {option.name}
                </option>
              ))}
            </select>
            <ChevronDown
              size={16}
              className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-black"
            />
          </div>

          <h2 className="text-xl font-semibold text-gray-900 border-b-2 border-gray-300 pb-0.5 mb-6">
            Access to Business Function
          </h2>
          <label className="ml-4 block text-sm font-semibold text-gray-700 mb-1">
            Owner
          </label>
          <input
            value={ownerEmail}
            onChange={(event) => setOwnerEmail(event.target.value)}
            placeholder="email@company.com"
            className="ml-4 w-[calc(95%-1rem)] border border-gray-300 rounded px-3 py-2 text-sm mb-4 placeholder:text-gray-400"
          />

          <label className="ml-4 block text-sm font-semibold text-gray-700 mb-1">
            Members of a Business Function
          </label>
          <input
            value={memberEmail1}
            onChange={(event) => setMemberEmail1(event.target.value)}
            placeholder="email@company.com"
            className="ml-4 w-[calc(95%-1rem)] border border-gray-300 rounded px-3 py-2 text-sm mb-2 placeholder:text-gray-400"
          />
          <input
            value={memberEmail2}
            onChange={(event) => setMemberEmail2(event.target.value)}
            placeholder="email@company.com"
            className="ml-4 w-[calc(95%-1rem)] border border-gray-300 rounded px-3 py-2 text-sm mb-2 placeholder:text-gray-400"
          />
          <input
            value={memberEmail3}
            onChange={(event) => setMemberEmail3(event.target.value)}
            placeholder="email@company.com"
            className="ml-4 w-[calc(95%-1rem)] border border-gray-300 rounded px-3 py-2 text-sm mb-2 placeholder:text-gray-400"
          />

          <hr className="border-gray-200 mt-6" />
        </>
      )}
    </div>
  )
}

export default IntakeForm

import { Send, Trash2, Share2, ChevronRight } from 'lucide-react'
import { sourceTypeLabels } from './SourceTypeDropdown.tsx'

const summarySections: {
  title: string
  fields: string[]
  expandable?: boolean
}[] = [
  {
    title: 'Intake Options',
    fields: ['Source type', 'Business Function', 'Access to Business Function'],
  },
  {
    title: 'Asset Ownership',
    fields: [
      'Information Asset Owner',
      'Data Owner',
      'Data Publisher Name',
      'Data Publisher email',
    ],
  },
  {
    title: 'Asset Identity',
    fields: [
      'Dataset Title',
      'Dataset Description',
      'Dataset Classification',
      'Contain PII data',
    ],
    expandable: true,
  },
  {
    title: 'Data Schema',
    fields: ['Number of Columns', 'Completed Schema for Columns'],
  },
  {
    title: 'Review',
    fields: ['Information Asset Owner', 'Data Owner'],
  },
  {
    title: 'Publication',
    fields: ['Approver', 'Current Action'],
  },
]

function SummaryPanel({ sourceType }: { sourceType: string | null }) {
  const sourceTypeLabel = sourceType ? sourceTypeLabels[sourceType] : undefined

  return (
    <div className="w-full h-full bg-white px-6 py-6 overflow-y-auto">
      <div className="flex items-center justify-between mb-1">
        <h2 className="text-base font-semibold text-gray-900">
          New Data Asset
        </h2>
        <span className="text-xs text-gray-400">Draft saved 14:55</span>
      </div>

      <div className="flex items-center gap-3 my-4">
        <button
          type="button"
          className="flex-1 bg-gray-200 text-gray-500 text-sm font-medium rounded-md py-2 cursor-not-allowed"
          disabled
        >
          Submit
        </button>
        <Send size={16} className="text-gray-400" />
        <Trash2 size={16} className="text-gray-400" />
        <Share2 size={16} className="text-gray-400" />
      </div>

      <h3 className="text-base font-semibold text-gray-900 mb-3 border-t border-gray-100 pt-4">
        Asset Summary
      </h3>

      <div className="space-y-5">
        {summarySections.map(({ title, fields, expandable }) => (
          <div key={title}>
            <p
              className={
                title === 'Intake Options'
                  ? 'text-xs font-bold uppercase tracking-wide text-gray-900 mb-1.5'
                  : 'text-xs font-semibold uppercase tracking-wide text-gray-500 mb-1.5'
              }
            >
              {title}
            </p>
            {title === 'Intake Options' ? (
              <div className="space-y-1">
                {fields.map((field) =>
                  field === 'Source type' ? (
                    <div
                      key={field}
                      className="flex items-center justify-between gap-2 text-xs text-gray-800"
                    >
                      <span>{field}</span>
                      {sourceTypeLabel && (
                        <span className="font-semibold text-gray-900">
                          {sourceTypeLabel}
                        </span>
                      )}
                    </div>
                  ) : (
                    <p key={field} className="text-xs text-gray-800">
                      {field}
                    </p>
                  ),
                )}
              </div>
            ) : (
              <ul className="space-y-1">
                {fields.map((field) => (
                  <li key={field} className="text-sm text-gray-800">
                    {field}
                  </li>
                ))}
              </ul>
            )}
            {expandable && (
              <button
                type="button"
                className="flex items-center gap-1 text-xs text-blue-800 font-medium mt-1"
              >
                <ChevronRight size={12} />
                More
              </button>
            )}
          </div>
        ))}
      </div>

      <div className="mt-5 border-t border-gray-100 pt-4">
        <p className="text-xs font-semibold uppercase tracking-wide text-gray-500 mb-1.5">
          Notes
        </p>
        <p className="text-sm text-gray-400">
          Here is the place for optional notes for the Approver
        </p>
      </div>
    </div>
  )
}

export default SummaryPanel

