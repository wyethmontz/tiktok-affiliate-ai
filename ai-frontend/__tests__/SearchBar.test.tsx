import { render, screen, act } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import SearchBar from "../app/components/SearchBar"

beforeEach(() => {
  jest.useFakeTimers()
})

afterEach(() => {
  jest.useRealTimers()
})

describe("SearchBar", () => {
  it("renders the input", () => {
    render(<SearchBar onSearch={jest.fn()} />)
    expect(screen.getByPlaceholderText("Search by product name...")).toBeInTheDocument()
  })

  it("calls onSearch with debounce after typing", async () => {
    const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime.bind(jest) })
    const onSearch = jest.fn()
    render(<SearchBar onSearch={onSearch} />)
    const input = screen.getByPlaceholderText("Search by product name...")

    await user.type(input, "serum")
    expect(onSearch).not.toHaveBeenCalled()

    act(() => jest.runAllTimers())
    expect(onSearch).toHaveBeenCalledWith("serum")
  })
})
