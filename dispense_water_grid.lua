points = api({
    method = "get",
    url = "/api/points"
})

function newPoint(x, y, z)
    return {
        x = x,
        y = y,
        z = z
    }
end

function findPointByName(points, name)
    for _, point in ipairs(points) do
        if point.name == name then
            return point
        end
    end
    return nil
end

local searchName = "plateau_03"
local refPoint = findPointByName(points, searchName)

if refPoint then
    send_message("info", "Found point:" .. refPoint.name)
else
    send_message("error", "No point found with the name:" .. searchName)
    return
end

local border_width = env("border_width")
local soil_sensor_offset = env("soil_sensor_offset")
local soil_sensor_height = env("soil_sensor_height")
local soil_measurement_depth = env("soil_measurement_depth")

local offset_x = env("padding_x") + border_width + soil_sensor_offset
local offset_y = env("padding_y") + border_width + soil_sensor_offset

local startPoint = newPoint(refPoint.x + offset_x, refPoint.y + offset_y, refPoint.z )

move_absolute (startPoint.x, startPoint.y, startPoint.z)

local tray_width = env("tray_width") - 3* border_width - 3 * soil_sensor_offset
local tray_length = env("tray_length") - 2 * border_width - 2 * soil_sensor_offset
local watering_offset = env("watering_offset")

local grid_points = {x = 3, y = 5, z = 1}

local spacing = {
    x = tray_width / (grid_points.x - 1),
    y = tray_length / (grid_points.y - 1),
    z = 0}

local grid = grid({
    grid_points = grid_points,
    spacing = spacing
})

local sensor_pin = 59

grid.each(function(cell)
    local currentPoint = newPoint(startPoint.x + cell.x, startPoint.y + cell.y, startPoint.z)

    toast("Moving to cell " .. cell.count .. ": (" .. currentPoint.x .. ", " .. currentPoint.y .. ", " .. currentPoint.z .. ")")

    move({
        x = currentPoint.x,
        y = currentPoint.y,
        z = currentPoint.z,
        speed = 100
    })

    move({
        z = startPoint.z - soil_measurement_depth
    })

    wait(500)

    local pin_value = read_pin(sensor_pin, "analog")
    local msg = "Soil moisture value: " .. pin_value

    send_message("info", msg)
    toast(msg)

    move({
        z = startPoint.z
    })

    if pin_value < 500 then
        move ({
            x = currentPoint.x + watering_offset
        })
        dispense(15)
    end

end)
